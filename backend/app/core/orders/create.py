"""Recording a sale from the tablet: priced, costed and taken out of stock on the server, never trusted from the client."""
import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import customers, visitors
from app.core.clock import as_aware, now
from app.core.catalog import branch_scope
from app.core.errors import DomainError
from app.core.orders.open_bills_visibility import INCLUDE_OPTION
from app.core.finance import session_control
from app.core.finance.payment_methods import missing_requirements
from app.core.money import ZERO
from app.core.orders import lines as line_rules
from app.core.orders import notes, overpayment, promo, stages, stations
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.order import Order
from app.models.payment_method import PaymentMethod
from app.models.promo import Promo
from app.models.user import User

PERMISSION = "order.buat"

NO_OPEN_SESSION = "Belum ada sesi yang dibuka. Buka sesi dulu sebelum membuat transaksi."
UNKNOWN_METHOD = "Metode pembayaran '{code}' tidak dikenal di cabang ini."
METHOD_NOT_READY = "Metode pembayaran {label} belum disetel (kurang: {missing}). Lengkapi dulu di menu Pembayaran."
METHOD_OFF = "Metode pembayaran '{label}' sedang dimatikan."
RECEIVED_REQUIRED = "Uang diterima wajib diisi untuk pembayaran {label}."
RECEIVED_TOO_LOW = "Uang diterima ({received}) kurang dari total ({total})."
PROMO_ENDED = "Promo yang dipilih sudah tidak berlaku. Pilih ulang promo di kasir."


@dataclass(frozen=True)
class NewOrder:
    """`client_id` makes a resend return the first order; `created_at` is the real time of a sale queued while offline."""

    client_id: str | None
    session_id: str | None
    order_type: str
    customer_name: str | None
    table_no: str | None
    payment_method: str
    cash_received: Decimal | None
    receipt_number: str | None
    created_at: datetime | None
    lines: list[line_rules.LineInput]
    visitor_category_id: str | None = None
    visitor_gender_id: str | None = None
    customer_id: str | None = None
    note_id: str | None = None
    note_label: str | None = None
    promo_id: str | None = None
    # Written and sent to the stations now, paid later: no method, no money yet (core.orders.open_bills).
    open_bill: bool = False


def _discount(db: Session, sale: NewOrder, written: line_rules.WrittenLines, day: date, outlet_id: str) -> tuple[str | None, Decimal]:
    """`day` is the session's business day; a live sale whose promo has ended, or belongs to another branch, is refused rather than charged differently from the screen, a queued one keeps the promo it was paid with."""
    if not sale.promo_id:
        return None, ZERO
    found = db.get(Promo, sale.promo_id)
    if sale.created_at is None:
        if found is None or not promo.is_in_effect(found, day) or not branch_scope.offered_at(found.outlet_id, outlet_id):
            raise DomainError(PROMO_ENDED)
        return found.id, promo.discount_of(found, written.promo_basis, written.subtotal, day)
    # A queued sale already happened, so only the promo's dates count, not a later switch-off.
    if found is None or not found.starts_on <= day <= found.ends_on:
        return None, ZERO
    return found.id, promo.discount_of(found, written.promo_basis, written.subtotal, day, ignore_switch=True)


def _existing(db: Session, client_id: str | None) -> Order | None:
    return db.scalar(select(Order).where(Order.client_id == client_id).execution_options(**{INCLUDE_OPTION: True})) if client_id else None


def _session(db: Session, user: User, requested: str | None) -> CashSession:
    """A queued order keeps its own session only while that session still runs; otherwise the cashier's running one, so a signed-off session never moves."""
    if requested:
        session = session_control.held(db, requested)
        if session is not None and session.cashier_id == user.id and session.status == CashSessionStatus.OPEN:
            return session
    session = session_control.running_of(db, user.id)
    if session is None:
        raise DomainError(NO_OPEN_SESSION)
    return session


def _sold_at(db: Session, sale_time: datetime, requested: str | None, session: CashSession) -> datetime:
    """A queued sale keeps the tablet's time, held between the opening of the session it was rung up in and now, so a wrong tablet clock never dates it outside its session or in the future."""
    opened = session.opened_at
    if requested and requested != session.id:
        opened = db.scalar(select(CashSession.opened_at).where(CashSession.id == requested)) or opened
    return min(max(as_aware(sale_time), as_aware(opened)), now())


def method_for(db: Session, outlet_id: str, code: str, queued: bool = False) -> PaymentMethod:
    method = db.scalar(select(PaymentMethod).where(PaymentMethod.outlet_id == outlet_id, PaymentMethod.code == code))
    if method is None:
        raise DomainError(UNKNOWN_METHOD.format(code=code))
    missing = missing_requirements(method)
    # A queued sale already happened, so neither an unfinished setup nor a later switch-off may refuse it; refusing would only lose it.
    if queued:
        return method
    if missing:
        raise DomainError(METHOD_NOT_READY.format(label=method.label, missing=", ".join(missing)))
    if not method.is_active:
        raise DomainError(METHOD_OFF.format(label=method.label))
    return method


def record(db: Session, user: User, sale: NewOrder) -> Order:
    found = _existing(db, sale.client_id)
    if found is not None:
        return found
    session = _session(db, user, sale.session_id)
    if sale.created_at is not None:
        sale = replace(sale, created_at=_sold_at(db, sale.created_at, sale.session_id, session))
    method = None if sale.open_bill else method_for(db, session.outlet_id, sale.payment_method, sale.created_at is not None)

    order = Order(
        id=str(uuid.uuid4()),
        client_id=sale.client_id,
        # Taken from the session, so the sale and the drawer it lands in always share a branch.
        outlet_id=session.outlet_id,
        cash_session_id=session.id,
        cashier_id=user.id,
        customer_name=(sale.customer_name or "").strip() or None,
        table_no=(sale.table_no or "").strip() or None,
        order_type=sale.order_type,
        receipt_number=sale.receipt_number,
        payment_method=method.code if method else None,
        payment_method_id=method.id if method else None,
        # Copied, so an old receipt keeps the method's name after the method is deleted.
        payment_method_label=method.label if method else None,
        is_open=sale.open_bill,
        discount=ZERO,
        partner_covered=ZERO,
        total=ZERO,
        created_at=sale.created_at or now(),
        serving_status=stages.first_code(db, session.outlet_id),
    )
    visitor = visitors.picked(db, session.outlet_id, sale.visitor_category_id, sale.visitor_gender_id)
    # Copied, so renaming or deleting a choice later leaves old orders and reports readable.
    if visitor.category is not None:
        order.visitor_category_id, order.visitor_category_label = visitor.category.id, visitor.category.name
    if visitor.gender is not None:
        order.visitor_gender_id, order.visitor_gender_label = visitor.gender.id, visitor.gender.name
    customer = customers.linked(db, sale.customer_id)
    if customer is not None:
        order.customer_id = customer.id
    note = notes.picked(db, sale.note_id, order.outlet_id)
    if note is not None:
        order.note_id, order.note_label = note.id, note.name
    elif sale.note_id and sale.note_label:
        # The choice was deleted after the cashier picked it: the order keeps the words the cashier saw.
        order.note_label = sale.note_label.strip()[: notes.MAX_NAME_LENGTH] or None
    db.add(order)
    try:
        # The cards written next point at the order, so it must exist first, inside the same transaction.
        db.flush()
    except IntegrityError:
        db.rollback()
        found = _existing(db, sale.client_id)
        if found is not None:
            return found
        raise

    written = line_rules.write(db, user, order, sale.lines, line_rules.Kept(), None, check_sellable=True)
    if sale.open_bill:
        # The promo and the method are chosen when the bill is paid.
        order.total = written.subtotal
    else:
        order.promo_id, order.discount = _discount(db, sale, written, session.business_day, session.outlet_id)
        order.total = max(ZERO, written.subtotal - order.discount)
    if method is not None:
        if method.needs_change:
            # Nothing is owed (a 100% promo), so there is nothing to receive and the cashier is not asked to type zero.
            received = sale.cash_received if sale.cash_received is not None else (ZERO if order.total == ZERO else None)
            if received is None:
                raise DomainError(RECEIVED_REQUIRED.format(label=method.label))
            if received < order.total:
                raise DomainError(RECEIVED_TOO_LOW.format(received=received, total=order.total))
            order.cash_received = received
        else:
            order.cash_received = order.total
        overpayment.sync(db, order, method)
    # A visit is a customer finishing an order, not merely being seen by the camera.
    if order.customer_id and not sale.open_bill:
        customers.count_visit(db, order.customer_id, order.outlet_id)
    stations.prepare_tasks(db, order)

    try:
        db.commit()
    except IntegrityError:
        # Two sends of the same client_id at once: the loser returns the winner instead of failing.
        db.rollback()
        found = _existing(db, sale.client_id)
        if found is not None:
            return found
        raise
    db.refresh(order)
    return order
