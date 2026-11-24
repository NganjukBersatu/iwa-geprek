"""Daftar pesanan satu sesi kasir, terbaru dulu dan berkursor, dengan pencarian ke seluruh isi pesanan."""
from dataclasses import dataclass

from sqlalchemy import String, cast, exists, or_, select, tuple_
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core import page_cursor, search
from app.core.orders import order_types
from app.core.orders.reading import OrderLines, lines_of
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_option import OrderItemOption
from app.models.user import User

MAX_QUERY_LENGTH = 100


@dataclass(frozen=True)
class SessionOrderPage:
    lines: list[OrderLines]
    next_cursor: str | None


def _scope(session_id: str, text: str) -> str:
    # Kursor terikat pada sesi dan kata yang dicari, supaya tidak bisa dipakai di daftar atau pencarian lain.
    return f"session-orders\0{session_id}\0{text}"


def _matches(text: str) -> ColumnElement[bool]:
    item_matches = exists().where(
        OrderItem.order_id == Order.id,
        or_(search.mentions(OrderItem.menu_item_name, text), search.mentions(OrderItem.note, text)),
    )
    option_matches = exists().where(
        OrderItem.order_id == Order.id,
        OrderItemOption.order_item_id == OrderItem.id,
        or_(search.mentions(OrderItemOption.name, text), search.mentions(OrderItemOption.group_name, text)),
    )
    cashier_matches = exists().where(
        User.id == Order.cashier_id,
        or_(search.mentions(User.name, text), search.mentions(User.username, text)),
    )
    return or_(
        search.mentions(Order.receipt_number, text),
        search.mentions(Order.customer_name, text),
        search.mentions(Order.table_no, text),
        search.mentions(Order.order_type, text),
        search.mentions(order_types.label_of(), text),
        search.mentions(Order.note_label, text),
        search.mentions(Order.payment_method_label, text),
        search.mentions(cast(Order.total, String), text),
        cashier_matches,
        item_matches,
        option_matches,
    )


def page_of(db: Session, session_id: str, query: str | None, cursor: str | None, limit: int) -> SessionOrderPage:
    """Empat query berapa pun ukuran halamannya; dibatasi ke satu sesi dulu lewat indeks shift_id, baru dicari."""
    text = (query or "").strip()
    scope = _scope(session_id, text)
    statement = select(Order).where(Order.cash_session_id == session_id)
    if text:
        statement = statement.where(_matches(text))
    if cursor:
        after = page_cursor.decode(scope, cursor)
        statement = statement.where(tuple_(Order.created_at, Order.id) < tuple_(after.at, after.id))
    found = list(db.scalars(statement.order_by(Order.created_at.desc(), Order.id.desc()).limit(limit + 1)).all())
    rows = found[:limit]
    next_cursor = None
    if len(found) > limit:
        last = rows[-1]
        next_cursor = page_cursor.encode(scope, page_cursor.Position(at=last.created_at, id=last.id))
    return SessionOrderPage(lines=lines_of(db, rows), next_cursor=next_cursor)
