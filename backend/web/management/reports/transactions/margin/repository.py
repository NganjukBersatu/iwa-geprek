"""Database reads of the margin report."""
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem


def margin_rows(db: Session, window: tuple) -> list[tuple]:
    """Grouped by the snapshotted name, since a menu removed from the catalog loses its id but keeps its name."""
    has_cost = OrderItem.unit_cost.is_not(None)
    return db.execute(
        select(
            func.max(OrderItem.menu_item_id),
            OrderItem.menu_item_name,
            func.sum(OrderItem.qty),
            func.sum(OrderItem.subtotal),
            func.sum(case((has_cost, OrderItem.unit_cost * OrderItem.qty), else_=0)),
            func.count(),
            func.sum(case((has_cost, 1), else_=0)),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(*window, Order.voided_at.is_(None))
        .group_by(OrderItem.menu_item_name)
        .order_by(func.sum(OrderItem.subtotal).desc(), OrderItem.menu_item_name)
    ).all()
