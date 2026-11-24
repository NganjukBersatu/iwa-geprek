"""An open bill: an order the stations already work on and the cashier pays later, in the same session.

Money is only counted once a bill is settled; until then it is hidden from every report and total (open_bills_visibility).
"""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import customers
from app.core.clock import now
from app.core.catalog import branch_scope
from app.core.errors import DomainError
from app.core.finance import session_control
from app.core.money import ZERO, decimal_of
from app.core.orders import create, overpayment, promo, stations
from app.core.orders import lines as line_rules
from app.core.orders import void
from app.core.orders.open_bills_visibility import INCLUDE_OPTION
from app.models.cash_session import CashSessionStatus
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.promo import Promo
from app.models.user import User

NOT_FOUND = 404
FORBIDDEN = 403
CONFLICT = 409
VERSION_MISMATCH = 412

BILL_NOT_FOUND = "Bill tidak ditemukan."
BILL_PAID = "Bill ini sudah dibayar."
BILL_VOIDED = "Bill ini sudah dibatalkan."
NOT_YOUR_BILL = "Bill ini milik sesi kasir lain. Hanya pemilik sesinya yang bisa mengubah atau membayarnya."
BILL_CHANGED = "Bill ini baru saja berubah. Muat ulang, periksa isinya, lalu coba lagi."
KEY_OF_OTHER_BILL = "Kunci pembayaran ini sudah dipakai untuk bill lain."


@dataclass(frozen=True)
class Settlement:
    """What the cashier picks at the counter; the total is worked out again from the bill itself."""

    payment_method: str
    cash_received: Decimal | None
    promo_id: str | None
    settle_key: str


def _open_query():
    return select(Order).where(Order.is_open.is_(True)).execution_options(**{INCLUDE_OPTION: True})


def of_outlet(db: Session, outlet_id: str) -> list[Order]:
    """Every open bill of a branch, oldest first, the other cashiers' ones included so the shift change sees them."""
    return list(db.scalars(_open_query().where(Order.outlet_id == outlet_id).order_by(Order.created_at, Order.id)).all())


def of_session(db: Session, session_id: str) -> list[Order]:
    """The bills of one session still unpaid, oldest first; the web shows them read-only beside the paid orders."""
    return list(db.scalars(_open_query().where(Order.cash_session_id == session_id).order_by(Order.created_at, Order.id)).all())


def _locked(db: Session, user: User, order_id: str, outlet_id: str | None) -> Order:
    """The bill, locked against a second cashier or tablet working on it at once; only its session owner changes it."""
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update().execution_options(**{INCLUDE_OPTION: True}))
    if order is None or (outlet_id and order.outlet_id != outlet_id):
        raise DomainError(BILL_NOT_FOUND, status=NOT_FOUND)
    if order.voided_at is not None:
        raise DomainError(BILL_VOIDED, status=CONFLICT)
    if not order.is_open:
        raise DomainError(BILL_PAID, status=CONFLICT)
    session = session_control.held(db, order.cash_session_id)
    if session is None or session.cashier_id != user.id or session.status != CashSessionStatus.OPEN:
        raise DomainError(NOT_YOUR_BILL, status=FORBIDDEN)
    return order


def _check_version(order: Order, expected: int) -> None:
    if order.version != expected:
        raise DomainError(BILL_CHANGED, status=VERSION_MISMATCH)


def add_lines(db: Session, user: User, order_id: str, outlet_id: str | None, expected_version: int, new_lines: list[line_rules.LineInput]) -> Order:
    """New menus join the bill at today's prices; the stations get tasks for the new lines only."""
    order = _locked(db, user, order_id, outlet_id)
    _check_version(order, expected_version)
    lines_before = stations.lines_before_edit(db, order)
    line_rules.write(db, user, order, new_lines, line_rules.Kept(), None, check_sellable=True)
    db.flush()
    items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    order.total = sum((item.subtotal for item in items), ZERO)
    order.version += 1
    stations.sync_after_edit(db, order, lines_before)
    db.commit()
    db.refresh(order)
    return order


@dataclass(frozen=True)
class Quote:
    """What the bill would cost with a promo; nothing is written."""

    subtotal: Decimal
    discount: Decimal
    total: Decimal
    promo_name: str | None


def _promo_of(db: Session, chosen_id: str | None, items: list[OrderItem], day, subtotal: Decimal, outlet_id: str) -> tuple[Promo | None, Decimal]:
    if not chosen_id:
        return None, ZERO
    chosen = db.get(Promo, chosen_id)
    if chosen is None or not promo.is_in_effect(chosen, day) or not branch_scope.offered_at(chosen.outlet_id, outlet_id):
        raise DomainError(create.PROMO_ENDED)
    basis = [(item.menu_item_id or "", item.unit_price * item.qty) for item in items]
    return chosen, promo.discount_of(chosen, basis, subtotal, day)


def quote(db: Session, user: User, order_id: str, outlet_id: str, promo_id: str | None) -> Quote:
    """The discount the server will apply at payment, so the tablet never works it out on its own."""
    order = _locked(db, user, order_id, outlet_id)
    session = session_control.held(db, order.cash_session_id)
    items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    subtotal = sum((item.subtotal for item in items), ZERO)
    chosen, discount = _promo_of(db, promo_id, items, session.business_day, subtotal, order.outlet_id)
    db.rollback()
    return Quote(subtotal, discount, max(ZERO, subtotal - discount - decimal_of(order.partner_covered)), chosen.name if chosen else None)


def _settled_by_key(db: Session, outlet_id: str, key: str) -> Order | None:
    return db.scalar(select(Order).where(Order.outlet_id == outlet_id, Order.settle_key == key).execution_options(**{INCLUDE_OPTION: True}))


def settle(db: Session, user: User, order_id: str, outlet_id: str, expected_version: int, payment: Settlement) -> Order:
    """Pays the bill with the same rules as a sale rung at the counter; a resend with the same key returns the first payment."""
    found = _settled_by_key(db, outlet_id, payment.settle_key)
    if found is not None:
        if found.id != order_id:
            raise DomainError(KEY_OF_OTHER_BILL, status=CONFLICT)
        return found

    order = _locked(db, user, order_id, outlet_id)
    _check_version(order, expected_version)
    session = session_control.held(db, order.cash_session_id)
    method = create.method_for(db, order.outlet_id, payment.payment_method)

    items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    subtotal = sum((item.subtotal for item in items), ZERO)
    chosen, discount = _promo_of(db, payment.promo_id, items, session.business_day, subtotal, order.outlet_id)
    promo_id = chosen.id if chosen else None

    order.promo_id, order.discount = promo_id, discount
    order.total = max(ZERO, subtotal - discount - decimal_of(order.partner_covered))
    order.payment_method, order.payment_method_id, order.payment_method_label = method.code, method.id, method.label
    if method.needs_change:
        received = payment.cash_received if payment.cash_received is not None else (ZERO if order.total == ZERO else None)
        if received is None:
            raise DomainError(create.RECEIVED_REQUIRED.format(label=method.label))
        if received < order.total:
            raise DomainError(create.RECEIVED_TOO_LOW.format(received=received, total=order.total))
        order.cash_received = received
    else:
        order.cash_received = order.total
    overpayment.sync(db, order, method)
    if order.customer_id:
        customers.count_visit(db, order.customer_id, order.outlet_id)
    order.is_open = False
    order.settled_at = now()
    order.settle_key = payment.settle_key
    order.version += 1
    db.commit()
    db.refresh(order)
    return order


def cancel(db: Session, user: User, order_id: str, outlet_id: str | None, reason: str | None) -> Order:
    """Nothing was paid, so no cancellation request is needed; stock and the stations' work are released by the shared void."""
    order = _locked(db, user, order_id, outlet_id)
    order.is_open = False
    order.version += 1
    void.apply_void(db, order, reason, user.id)
    db.commit()
    db.refresh(order)
    return order
