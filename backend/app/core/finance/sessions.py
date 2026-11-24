"""The one door for correcting and deleting cash sessions and their orders; derived figures are worked out again, never typed."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.finance.session_totals import refresh_closed
from app.core.orders import cancellations
from app.core.orders.void import PERMISSION_VOID_CLOSED, apply_void
from app.models.benefit_usage import BenefitUsage
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.expense import Expense
from app.models.ingredient import IngredientCard
from app.models.order import Order
from app.models.user import User
from app.models.stock import StockCard

PERMISSION_CORRECT = "sesi.koreksi"
PERMISSION_DELETE = "sesi.hapus"
PERMISSION_OWN = "sesi.kelola_sendiri"
PERMISSION_DELETE_ORDER = "transaksi.hapus"
PERMISSION_EDIT_ORDER = "transaksi.ubah"
MIN_VOID_REASON = 3

BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404

SESSION_NOT_FOUND = "Sesi tidak ditemukan."
ORDER_NOT_FOUND = "Transaksi tidak ditemukan."
NO_PERMISSION = "Peran '{role}' tidak punya izin '{permission}'."
OWN_ONLY = "Izin 'sesi.kelola_sendiri' hanya berlaku untuk sesi sendiri."
RUNNING_ONLY = "Izin 'sesi.kelola_sendiri' hanya berlaku selama sesi masih berjalan."
ACTUAL_AFTER_CLOSE = "Uang aktual baru ada setelah sesi ditutup."
THREE_PARTS = "Sesi ini memakai tiga bagian uang (modal, belanja, omzet), jadi uang aktual tidak bisa diubah dengan satu angka."
ORDER_LOCKED = "Transaksi ini sedang menunggu keputusan pembatalan. Selesaikan pengajuannya dulu."
ORDER_VOIDED = "Transaksi ini sudah dibatalkan."
VOID_REASON_SHORT = "Tulis alasan pembatalan, minimal 3 huruf."
VOID_CLOSED_SESSION = "Sesinya sudah ditutup. Membatalkan transaksinya butuh izin 'order.void_shift_tutup'."


@dataclass(frozen=True)
class SessionImpact:
    orders: int
    expenses: int


def _check_may_manage(user: User, session: CashSession | None, permission_all: str) -> None:
    """Two ways in only: the permission for every session, or managing one's own session while it still runs."""
    if user.allows(permission_all):
        return
    if not user.allows(PERMISSION_OWN):
        raise DomainError(NO_PERMISSION.format(role=user.role.name if user.role else "-", permission=permission_all), status=FORBIDDEN)
    if session is None or session.cashier_id != user.id:
        raise DomainError(OWN_ONLY, status=FORBIDDEN)
    if session.status != CashSessionStatus.OPEN:
        raise DomainError(RUNNING_ONLY, status=FORBIDDEN)


def _session(db: Session, session_id: str, outlet_id: str | None) -> CashSession:
    session = db.get(CashSession, session_id)
    # Another branch's session answers as missing, so its existence is not revealed.
    if session is None or (outlet_id and session.outlet_id != outlet_id):
        raise DomainError(SESSION_NOT_FOUND, status=NOT_FOUND)
    return session


def correct(
    db: Session,
    user: User,
    session_id: str,
    outlet_id: str | None,
    opening_cash: Decimal | None,
    actual_cash: Decimal | None,
    note: str | None,
    note_sent: bool,
) -> CashSession:
    session = _session(db, session_id, outlet_id)
    _check_may_manage(user, session, PERMISSION_CORRECT)
    if actual_cash is not None and session.status != CashSessionStatus.CLOSED:
        raise DomainError(ACTUAL_AFTER_CLOSE)
    if actual_cash is not None and session.planned_shopping is not None:
        raise DomainError(THREE_PARTS)
    if opening_cash is not None:
        session.opening_cash = opening_cash
    if actual_cash is not None:
        session.actual_cash = actual_cash
    if note_sent:
        session.note = (note or "").strip() or None
    refresh_closed(db, session)
    db.commit()
    db.refresh(session)
    return session


def impact(db: Session, user: User, session_id: str, outlet_id: str | None) -> SessionImpact:
    session = _session(db, session_id, outlet_id)
    _check_may_manage(user, session, PERMISSION_DELETE)
    orders = db.scalar(select(func.count()).select_from(Order).where(Order.cash_session_id == session.id)) or 0
    expenses = db.scalar(select(func.count()).select_from(Expense).where(Expense.cash_session_id == session.id)) or 0
    return SessionImpact(orders=orders, expenses=expenses)


def _remove_order(db: Session, order: Order) -> None:
    """Its benefit usages, ingredient and stock cards go too, so warehouse balances return as if the sale never happened."""
    db.execute(delete(BenefitUsage).where(BenefitUsage.order_id == order.id))
    db.execute(delete(IngredientCard).where(IngredientCard.order_id == order.id))
    db.execute(delete(StockCard).where(StockCard.order_id == order.id))
    db.delete(order)


def _remove_orders_of(db: Session, session_id: str) -> None:
    """All the orders of one session with their cards, in four statements however many orders it holds."""
    orders = select(Order.id).where(Order.cash_session_id == session_id)
    db.execute(delete(BenefitUsage).where(BenefitUsage.order_id.in_(orders)))
    db.execute(delete(IngredientCard).where(IngredientCard.order_id.in_(orders)))
    db.execute(delete(StockCard).where(StockCard.order_id.in_(orders)))
    db.execute(delete(Order).where(Order.cash_session_id == session_id))


def delete_session(db: Session, user: User, session_id: str, outlet_id: str | None) -> None:
    """Its orders go with it; its expenses stay but lose the session, since that money really left the drawer."""
    session = _session(db, session_id, outlet_id)
    _check_may_manage(user, session, PERMISSION_DELETE)
    _remove_orders_of(db, session.id)
    db.execute(update(Expense).where(Expense.cash_session_id == session.id).values(cash_session_id=None))
    db.delete(session)
    db.commit()


def ensure_not_locked(db: Session, order: Order) -> None:
    """An order waiting for a cancellation decision may not be changed or deleted."""
    if cancellations.has_pending(db, order.id):
        raise DomainError(ORDER_LOCKED)


def ensure_may_edit_order(db: Session, user: User, order: Order) -> CashSession | None:
    """Same two doors as deleting: the permission for every session, or one's own running session."""
    session = db.get(CashSession, order.cash_session_id) if order.cash_session_id else None
    _check_may_manage(user, session, PERMISSION_EDIT_ORDER)
    return session


def delete_order(db: Session, user: User, order_id: str, outlet_id: str | None) -> None:
    """Allowed in a closed session too; its frozen figures are worked out again afterwards."""
    order = db.get(Order, order_id)
    if order is None or (outlet_id and order.outlet_id != outlet_id):
        raise DomainError(ORDER_NOT_FOUND, status=NOT_FOUND)
    session = db.get(CashSession, order.cash_session_id) if order.cash_session_id else None
    _check_may_manage(user, session, PERMISSION_DELETE_ORDER)
    ensure_not_locked(db, order)
    _remove_order(db, order)
    if session is not None:
        refresh_closed(db, session)
    db.commit()


def void_order(db: Session, user: User, order_id: str, outlet_id: str | None, reason: str) -> Order:
    """A cancellation by an admin, without a request; the order stays as a record and a closed session's figures are worked out again."""
    order = db.get(Order, order_id)
    if order is None or (outlet_id and order.outlet_id != outlet_id):
        raise DomainError(ORDER_NOT_FOUND, status=NOT_FOUND)
    if order.voided_at is not None:
        raise DomainError(ORDER_VOIDED)
    if len(reason.strip()) < MIN_VOID_REASON:
        raise DomainError(VOID_REASON_SHORT)
    session = db.get(CashSession, order.cash_session_id) if order.cash_session_id else None
    if session is not None and session.status == CashSessionStatus.CLOSED and not user.allows(PERMISSION_VOID_CLOSED):
        raise DomainError(VOID_CLOSED_SESSION, status=FORBIDDEN)
    ensure_not_locked(db, order)
    apply_void(db, order, reason, user.id)
    if session is not None:
        refresh_closed(db, session)
    db.commit()
    return order
