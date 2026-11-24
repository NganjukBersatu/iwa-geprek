"""Database reads of the busy-products report."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.order import Order
from app.models.order_item import OrderItem
from app.core.sql_time import wib_hour
from web.management.reports.menu.busy_sales.repository import moment_of, slot_columns
from web.management.reports.menu.time_slots import Moment


def line_totals(db: Session, conditions: tuple) -> tuple:
    """Total qty and total subtotal of every sold line."""
    return db.execute(
        select(
            func.coalesce(func.sum(OrderItem.qty), 0),
            func.coalesce(func.sum(OrderItem.subtotal), 0),
        )
        .select_from(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .where(*conditions)
    ).one()


def product_lines(db: Session, conditions: tuple, search: str | None, hour: int | None, with_minute: bool) -> list[tuple[str, Moment, object, object, int]]:
    """(menu name, moment, qty, subtotal, orders) grouped in SQL, optionally narrowed by name and by one hour: one query, however many lines there are."""
    filters = list(conditions)
    if search and search.strip():
        filters.append(contains(OrderItem.menu_item_name, search.strip()))
    if hour is not None:
        filters.append(wib_hour(Order.created_at) == hour)
    columns = slot_columns(with_minute)
    rows = db.execute(
        select(OrderItem.menu_item_name, *columns, func.sum(OrderItem.qty), func.sum(OrderItem.subtotal), func.count(func.distinct(Order.id)))
        .join(Order, OrderItem.order_id == Order.id)
        .where(*filters)
        .group_by(OrderItem.menu_item_name, *columns)
    ).all()
    width = len(columns)
    return [(row[0], moment_of(row[1:], with_minute), row[1 + width], row[2 + width], row[3 + width]) for row in rows]
