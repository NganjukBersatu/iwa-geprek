"""Correcting the content of an order: header, payment, and lines. Number and time stay; everything derived is worked out again."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.finance import sessions
from app.core.finance.session_totals import refresh_closed
from app.core.money import ZERO, decimal_of
from app.core.orders import lines as line_rules
from app.core.orders import overpayment, promo, stations
from app.models.ingredient import IngredientCard
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_option import EXTRA, OrderItemOption
from app.models.payment_method import PaymentMethod
from app.models.promo import Promo
from app.models.user import User
from app.models.stock import StockCard

NOT_FOUND = 404
ORDER_NOT_FOUND = "Transaksi tidak ditemukan."
ORDER_VOIDED = "Transaksi yang sudah dibatalkan tidak bisa diedit."
PARTNER_LOCKED = "Transaksi dengan benefit mitra tidak bisa diubah isinya. Batalkan lalu buat ulang."
UNKNOWN_METHOD = "Metode pembayaran '{code}' tidak dikenal di cabang ini."
RECEIVED_TOO_LOW = "Uang diterima ({received}) kurang dari total baru ({total})."
CORRECTION_NOTE = "Koreksi transaksi"


@dataclass(frozen=True)
class OrderChange:
    """What is not sent is not changed; `lines` replaces every line of the order."""

    customer_name: str | None = None
    table_no: str | None = None
    order_type: str | None = None
    payment_method: str | None = None
    cash_received: Decimal | None = None
    lines: list[line_rules.LineInput] | None = None
    promo_id: str | None = None
    remove_promo: bool = False


def _method(db: Session, outlet_id: str, code: str | None) -> PaymentMethod | None:
    return db.scalar(select(PaymentMethod).where(PaymentMethod.outlet_id == outlet_id, PaymentMethod.code == code))


def _replace_lines(db: Session, user: User, order: Order, lines: list[line_rules.LineInput]) -> tuple[list[tuple[str, Decimal]], Decimal]:
    """Removes the old lines and their cards, then writes the new ones at the prices the old ones were sold at."""
    old_items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    old_options = db.scalars(select(OrderItemOption).where(OrderItemOption.order_item_id.in_([item.id for item in old_items]))).all() if old_items else []
    options_of: dict[str, list[OrderItemOption]] = {}
    for option in old_options:
        options_of.setdefault(option.order_item_id, []).append(option)

    sold: dict[str, line_rules.SoldAt] = {}
    kept_extra_prices: dict[str, Decimal] = {}
    for item in old_items:
        own = options_of.get(item.id, [])
        added_cost = sum(((option.unit_cost or ZERO) * option.qty for option in own), ZERO)
        if item.menu_item_id:
            sold[item.menu_item_id] = line_rules.SoldAt(item.unit_price, None if item.unit_cost is None else item.unit_cost - added_cost)
        for option in own:
            if option.kind == EXTRA and option.ref_id:
                kept_extra_prices.setdefault(option.ref_id, option.price)

    db.execute(delete(IngredientCard).where(IngredientCard.order_id == order.id))
    db.execute(delete(StockCard).where(StockCard.order_id == order.id))
    if old_items:
        db.execute(delete(OrderItemOption).where(OrderItemOption.order_item_id.in_([item.id for item in old_items])))
    db.execute(delete(OrderItem).where(OrderItem.order_id == order.id))
    db.flush()

    written = line_rules.write(db, user, order, lines, line_rules.Kept(sold, kept_extra_prices), CORRECTION_NOTE, check_sellable=False)
    return written.promo_basis, written.subtotal


def edit_order(db: Session, user: User, order_id: str, outlet_id: str | None, change: OrderChange) -> Order:
    order = db.get(Order, order_id)
    if order is None or (outlet_id and order.outlet_id != outlet_id):
        raise DomainError(ORDER_NOT_FOUND, status=NOT_FOUND)
    session = sessions.ensure_may_edit_order(db, user, order)
    if order.voided_at is not None:
        raise DomainError(ORDER_VOIDED)
    sessions.ensure_not_locked(db, order)
    changes_money = change.lines is not None or change.payment_method is not None or change.promo_id is not None or change.remove_promo
    # Partner benefit is already on the foundation's bill; the content and payment must not drift silently.
    if decimal_of(order.partner_covered) > 0 and changes_money:
        raise DomainError(PARTNER_LOCKED)

    if change.customer_name is not None:
        order.customer_name = change.customer_name.strip() or None
    if change.table_no is not None:
        order.table_no = change.table_no.strip() or None
    if change.order_type is not None:
        order.order_type = change.order_type

    if change.payment_method is not None and change.payment_method != order.payment_method:
        method = _method(db, order.outlet_id, change.payment_method)
        if method is None:
            raise DomainError(UNKNOWN_METHOD.format(code=change.payment_method))
        order.payment_method = method.code
        order.payment_method_id = method.id
        order.payment_method_label = method.label

    # Dibaca sebelum baris ditulis ulang supaya pekerjaan stasiun pada baris yang tetap tidak hilang.
    lines_before = stations.lines_before_edit(db, order) if change.lines is not None else None
    if change.lines is not None:
        promo_basis, subtotal = _replace_lines(db, user, order, change.lines)
    else:
        existing = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        promo_basis = [(item.menu_item_id or "", item.unit_price * item.qty) for item in existing]
        subtotal = sum((item.subtotal for item in existing), ZERO)

    if change.remove_promo:
        order.promo_id = None
    elif change.promo_id is not None:
        order.promo_id = change.promo_id
    discount = ZERO
    if order.promo_id:
        found = db.get(Promo, order.promo_id)
        if found is not None:
            discount = promo.discount_of(found, promo_basis, subtotal, order.business_day)
        else:
            order.promo_id = None
    order.discount = discount
    order.total = max(ZERO, subtotal - discount - decimal_of(order.partner_covered))

    method = _method(db, order.outlet_id, order.payment_method)
    if method is not None and method.needs_change:
        received = change.cash_received if change.cash_received is not None else order.cash_received
        if received is None or received < order.total:
            raise DomainError(RECEIVED_TOO_LOW.format(received=received or 0, total=order.total))
        order.cash_received = received
    else:
        order.cash_received = order.total

    overpayment.sync(db, order, method)
    db.flush()
    stations.sync_after_edit(db, order, lines_before)
    if session is not None:
        refresh_closed(db, session)
    db.commit()
    db.refresh(order)
    return order
