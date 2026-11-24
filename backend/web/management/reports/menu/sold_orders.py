"""Filters and counts of sold orders that several menu reports read."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.money import decimal_of
from app.models.order import Order
from app.models.order_item import OrderItem


def count_orders(db: Session, conditions: tuple) -> int:
    return int(db.scalar(select(func.count()).select_from(Order).where(*conditions)) or 0)


def _has_lines():
    return select(1).where(OrderItem.order_id == Order.id).exists()


def count_orders_with_lines(db: Session, conditions: tuple) -> int:
    """Orders that carry at least one line: the only ones a report built from lines can ever show."""
    return int(db.scalar(select(func.count()).select_from(Order).where(*conditions, _has_lines())) or 0)


def orders_without_lines(db: Session, conditions: tuple) -> tuple[int, Decimal]:
    """Count and total of orders with no line at all; line-based reports leave them out while sales reports count them."""
    count, total = db.execute(
        select(func.count(), func.coalesce(func.sum(Order.total), 0)).select_from(Order).where(*conditions, ~_has_lines())
    ).one()
    return int(count or 0), decimal_of(total)
