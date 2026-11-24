"""Database reads of the busy-sales report."""
from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from app.core.sql_time import wib_hour, wib_minute
from app.models.order import Order
from app.models.order_item import OrderItem
from web.management.reports.menu.time_slots import Moment


def slot_columns(with_minute: bool) -> list:
    """The finest moment any unit of the report needs: the business day and sale hour, or the minute when one hour is dived into."""
    columns = [Order.business_day, wib_hour(Order.created_at)]
    return columns + [wib_minute(Order.created_at)] if with_minute else columns


def moment_of(row: tuple, with_minute: bool) -> Moment:
    return Moment(row[0], row[1], row[2] if with_minute else 0)


def order_sales(db: Session, conditions: tuple, hour: int | None, with_minute: bool) -> list[tuple[Moment, str | None, int, object]]:
    """(moment, customer_id, orders, sales) grouped in SQL: one query, however many orders there are."""
    columns = slot_columns(with_minute)
    focus = wib_hour(Order.created_at) == hour if hour is not None else true()
    rows = db.execute(
        select(*columns, Order.customer_id, func.count(), func.sum(Order.total)).where(*conditions, focus).group_by(*columns, Order.customer_id)
    ).all()
    width = len(columns)
    return [(moment_of(row, with_minute), row[width], row[width + 1], row[width + 2]) for row in rows]


def line_quantities(db: Session, conditions: tuple, hour: int | None, with_minute: bool) -> list[tuple[Moment, object]]:
    """(moment, units sold) grouped in SQL."""
    columns = slot_columns(with_minute)
    focus = wib_hour(Order.created_at) == hour if hour is not None else true()
    rows = db.execute(
        select(*columns, func.sum(OrderItem.qty)).join(Order, OrderItem.order_id == Order.id).where(*conditions, focus).group_by(*columns)
    ).all()
    width = len(columns)
    return [(moment_of(row, with_minute), row[width]) for row in rows]
