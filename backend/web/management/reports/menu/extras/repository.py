"""Database reads of the extras report."""
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_option import EXTRA, OrderItemOption


def line_revenue(db: Session, conditions: tuple):
    return db.scalar(
        select(func.coalesce(func.sum(OrderItem.subtotal), 0))
        .select_from(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .where(*conditions)
    )


def extra_sales(db: Session, conditions: tuple) -> list:
    """Quantity, transactions, revenue at the price sold, and known cost per extra."""
    units = OrderItemOption.qty * OrderItem.qty
    costed = OrderItemOption.unit_cost.is_not(None)
    return db.execute(
        select(
            OrderItemOption.name.label("extra_name"),
            func.coalesce(func.sum(units), 0).label("quantity"),
            func.count(func.distinct(OrderItem.order_id)).label("transactions"),
            func.coalesce(func.sum(OrderItemOption.price * units), 0).label("revenue"),
            func.coalesce(func.sum(case((costed, OrderItemOption.unit_cost * units), else_=0)), 0).label("cost"),
            func.coalesce(func.sum(case((costed, OrderItemOption.price * units), else_=0)), 0).label("costed_revenue"),
            func.coalesce(func.sum(case((costed, 1), else_=0)), 0).label("costed_lines"),
        )
        .select_from(OrderItemOption)
        .join(OrderItem, OrderItemOption.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItemOption.kind == EXTRA, *conditions)
        .group_by(OrderItemOption.name)
    ).all()
