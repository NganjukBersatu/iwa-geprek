"""Database reads of the comparison: money by business day, optionally only what was written before a cut; visits by their own time."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.branches import branch_filter
from app.core.business_days import expenses_in, valid_orders_in
from app.core.date_range import range_end, range_start
from app.core.money import decimal_of
from app.models.expense import Expense
from app.models.order import Order
from app.models.visit import Visit


def _before(column, cut: datetime | None) -> tuple:
    return () if cut is None else (column < cut,)


def income(db: Session, start: date, end: date, cut: datetime | None, outlet_id: str | None) -> tuple[Decimal, int]:
    total, count = db.execute(
        select(func.coalesce(func.sum(Order.total), 0), func.count()).where(
            *valid_orders_in(start, end, outlet_id), *_before(Order.created_at, cut)
        )
    ).one()
    return decimal_of(total), int(count or 0)


def expense_total(db: Session, start: date, end: date, cut: datetime | None, outlet_id: str | None) -> Decimal:
    return decimal_of(
        db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                *expenses_in(start, end, outlet_id), *_before(Expense.created_at, cut)
            )
        )
    )


def distinct_visitors(db: Session, start: date, end: date, cut: datetime | None, outlet_id: str | None) -> int:
    return int(
        db.scalar(
            select(func.count(func.distinct(Visit.customer_id))).where(
                Visit.visited_at >= range_start(start),
                Visit.visited_at < range_end(end),
                *_before(Visit.visited_at, cut),
                *branch_filter(Visit.outlet_id, outlet_id),
            )
        )
        or 0
    )
