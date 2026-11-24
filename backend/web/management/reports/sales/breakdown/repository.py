"""Database reads of the sales breakdown, one grouped query per source so joins cannot multiply sums."""
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import decimal_of
from app.models.order import Order
from app.models.order_item import OrderItem


def sales_by_order_type(db: Session, start: date, end: date, outlet_id: str | None) -> dict[str, tuple[int, Decimal]]:
    return {
        order_type: (count, decimal_of(total))
        for order_type, count, total in db.execute(
            select(Order.order_type, func.count(), func.sum(Order.total))
            .where(*valid_orders_in(start, end, outlet_id))
            .group_by(Order.order_type)
        ).all()
    }


def sales_by_outlet(db: Session, start: date, end: date) -> dict[str, tuple[int, Decimal]]:
    return {
        outlet_id: (count, decimal_of(total))
        for outlet_id, count, total in db.execute(
            select(Order.outlet_id, func.count(), func.sum(Order.total))
            .where(*valid_orders_in(start, end, None))
            .group_by(Order.outlet_id)
        ).all()
    }


def line_profit_by_outlet(db: Session, start: date, end: date) -> dict[str, Decimal | None]:
    """Line revenue minus cost per branch; None when any line has no recorded cost."""
    has_cost = OrderItem.unit_cost.is_not(None)
    return {
        outlet_id: (decimal_of(revenue) - decimal_of(cost) if uncosted == 0 else None)
        for outlet_id, revenue, cost, uncosted in db.execute(
            select(
                Order.outlet_id,
                func.sum(OrderItem.subtotal),
                func.sum(case((has_cost, OrderItem.unit_cost * OrderItem.qty), else_=0)),
                func.sum(case((has_cost, 0), else_=1)),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(*valid_orders_in(start, end, None))
            .group_by(Order.outlet_id)
        ).all()
    }
