"""Database reads of the kitchen report."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.sql_time import seconds_between, wib_hour
from app.models.order import Order
from web.management.reports.menu.sold_orders import count_orders


def duration_groups(db: Session, conditions: tuple) -> list[tuple[int, int, bool, int]]:
    """(WIB hour, whole seconds, whether the time was a whole number of seconds, orders) of the served orders: one grouped query.

    The report rounds each order's minutes, so the exact seconds are kept in whole-second buckets with a flag for the exact ones;
    the rounding itself is done by the service with the same arithmetic as before.
    """
    seconds = seconds_between(Order.created_at, Order.served_at)
    whole = func.floor(seconds)
    exact = seconds == whole
    hour = wib_hour(Order.created_at)
    rows = db.execute(
        select(hour, whole, exact, func.count()).where(*conditions, Order.served_at.is_not(None)).group_by(hour, whole, exact)
    ).all()
    return [(int(row_hour), int(row_whole), bool(row_exact), int(count)) for row_hour, row_whole, row_exact, count in rows]


def slowest_orders(db: Session, conditions: tuple, limit: int) -> list:
    """(id, customer name, table, created_at, served_at) of the slowest served orders."""
    return db.execute(
        select(Order.id, Order.customer_name, Order.table_no, Order.created_at, Order.served_at)
        .where(*conditions, Order.served_at.is_not(None))
        .order_by(seconds_between(Order.created_at, Order.served_at).desc())
        .limit(limit)
    ).all()


def count_unserved(db: Session, conditions: tuple) -> int:
    return count_orders(db, (*conditions, Order.served_at.is_(None)))
