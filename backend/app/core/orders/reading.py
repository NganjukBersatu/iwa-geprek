"""Orders read back with their lines and the variants and extras chosen on them; the session history screen and the tablet both read it."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_option import OrderItemOption
from app.models.promo import Promo


@dataclass(frozen=True)
class OrderLines:
    order: Order
    items: list[OrderItem]
    options: dict[str, list[OrderItemOption]]
    promo_name: str | None = None


def lines_of(db: Session, orders: list[Order]) -> list[OrderLines]:
    """Each order with its own lines and the variants and extras chosen on them, in four queries; the promo name is read so a reprint can still name the promo."""
    items: dict[str, list[OrderItem]] = {order.id: [] for order in orders}
    options: dict[str, list[OrderItemOption]] = {}
    if orders:
        found = db.scalars(select(OrderItem).where(OrderItem.order_id.in_(list(items))).order_by(OrderItem.id)).all()
        for item in found:
            items[item.order_id].append(item)
        if found:
            for option in db.scalars(select(OrderItemOption).where(OrderItemOption.order_item_id.in_([item.id for item in found]))).all():
                options.setdefault(option.order_item_id, []).append(option)
    promo_ids = {order.promo_id for order in orders if order.promo_id}
    promo_names = dict(db.execute(select(Promo.id, Promo.name).where(Promo.id.in_(promo_ids))).all()) if promo_ids else {}
    return [OrderLines(order, items[order.id], options, promo_names.get(order.promo_id) if order.promo_id else None) for order in orders]


def orders_of(db: Session, session_id: str) -> list[OrderLines]:
    """Every order of the session, oldest first."""
    orders = db.scalars(select(Order).where(Order.cash_session_id == session_id).order_by(Order.created_at, Order.id)).all()
    return lines_of(db, list(orders))
