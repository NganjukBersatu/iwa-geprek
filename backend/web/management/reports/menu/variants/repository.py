"""Database reads of the variants report."""
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_option import VARIANT, OrderItemOption


def variant_sales(db: Session, conditions: tuple, by_menu: bool) -> list:
    """Portions, transactions, revenue, and known cost per variant option, optionally split per menu."""
    keys = [OrderItemOption.group_name, OrderItemOption.name]
    if by_menu:
        keys.append(OrderItem.menu_item_name)
    costed = OrderItem.unit_cost.is_not(None)
    return db.execute(
        select(
            OrderItemOption.group_name.label("group_name"),
            OrderItemOption.name.label("option_name"),
            *([OrderItem.menu_item_name.label("menu_item_name")] if by_menu else []),
            func.coalesce(func.sum(OrderItem.qty), 0).label("portions"),
            func.count(func.distinct(OrderItem.order_id)).label("transactions"),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("revenue"),
            func.coalesce(func.sum(case((costed, OrderItem.unit_cost * OrderItem.qty), else_=0)), 0).label("cost"),
            func.coalesce(func.sum(case((costed, OrderItem.subtotal), else_=0)), 0).label("costed_revenue"),
            func.coalesce(func.sum(case((costed, 1), else_=0)), 0).label("costed_lines"),
        )
        .select_from(OrderItemOption)
        .join(OrderItem, OrderItemOption.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItemOption.kind == VARIANT, *conditions)
        .group_by(*keys)
    ).all()
