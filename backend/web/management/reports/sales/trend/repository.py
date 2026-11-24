"""Database reads of the trend: money in bars of business days, visits in bars of their own time."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, case, func, literal, or_, select
from sqlalchemy.orm import Session, aliased

from app.core.branches import branch_filter
from app.core.business_days import expenses_in, valid_orders_in
from app.core.date_range import range_end, range_start
from app.core.money import decimal_of
from app.models.expense import Expense
from app.models.order import Order
from app.models.visit import Visit
from web.management.reports.sales.trend.domain import Bar


def _day(day: date) -> date:
    return day


def _next_day(day: date) -> date:
    return day + timedelta(days=1)


def _bar_of(column, bars: list[Bar], values=None, low=range_start, high=range_end):
    """SQL expression: the bar index (or `values[i]`) a time or business day falls in; -1 (or NULL) outside them all."""
    return case(
        *[
            (
                and_(column >= low(bar.start), column < high(bar.end)),
                i if values is None else values[i],
            )
            for i, bar in enumerate(bars)
        ],
        else_=-1 if values is None else None,
    )


def trend_figures(
    db: Session, bars: list[Bar], outlet_id: str | None
) -> tuple[dict[int, Decimal], dict[int, int], dict[int, Decimal], dict[int, tuple[int, int]]]:
    """Income, order count, expense, and (unique, returning) customers of every bar, keyed by bar index."""
    first = min(bar.start for bar in bars)
    last = max(bar.end for bar in bars)
    low, high = range_start(first), range_end(last)

    # A subquery first, because Postgres treats the parameterised bar expression in SELECT and GROUP BY as two expressions.
    base = (
        select(_bar_of(Order.business_day, bars, low=_day, high=_next_day).label("b"), Order.total.label("v"))
        .where(*valid_orders_in(first, last, outlet_id))
        .subquery()
    )
    income_by_bar: dict[int, Decimal] = {}
    order_count_by_bar: dict[int, int] = {}
    for bar, total, count in db.execute(
        select(base.c.b, func.sum(base.c.v), func.count(base.c.v)).group_by(base.c.b)
    ).all():
        income_by_bar[bar] = decimal_of(total)
        order_count_by_bar[bar] = count

    base = (
        select(_bar_of(Expense.business_day, bars, low=_day, high=_next_day).label("b"), Expense.amount.label("v"))
        .where(*expenses_in(first, last, outlet_id))
        .subquery()
    )
    expense_by_bar = {
        bar: decimal_of(value)
        for bar, value in db.execute(select(base.c.b, func.sum(base.c.v)).group_by(base.c.b)).all()
    }

    in_range = (
        Visit.visited_at >= low,
        Visit.visited_at < high,
        *branch_filter(Visit.outlet_id, outlet_id),
    )
    earlier = aliased(Visit)
    seen_before_range = select(1).where(earlier.customer_id == Visit.customer_id, earlier.visited_at < low).exists()
    # A visit at any branch makes a returning customer, but only customers who came to the requested branch count.
    any_branch = (Visit.visited_at >= low, Visit.visited_at < high)
    if outlet_id is not None:
        any_branch = (*any_branch, Visit.customer_id.in_(select(Visit.customer_id).where(*in_range)))
    per_customer = (
        select(
            Visit.customer_id.label("c"),
            func.min(Visit.visited_at).label("m"),
            seen_before_range.label("seen"),
        )
        .where(*any_branch)
        .group_by(Visit.customer_id)
        .subquery()
    )
    bar_start = _bar_of(
        Visit.visited_at,
        bars,
        [literal(range_start(bar.start), Visit.visited_at.type) for bar in bars],
    )
    rows = (
        select(
            _bar_of(Visit.visited_at, bars).label("b"),
            bar_start.label("s"),
            Visit.customer_id.label("c"),
        )
        .where(*in_range)
        .subquery()
    )
    customers_by_bar = {
        bar: (unique or 0, returning or 0)
        for bar, unique, returning in db.execute(
            select(
                rows.c.b,
                func.count(func.distinct(rows.c.c)),
                func.count(func.distinct(case((or_(per_customer.c.seen, per_customer.c.m < rows.c.s), rows.c.c)))),
            )
            .select_from(rows)
            .join(per_customer, per_customer.c.c == rows.c.c)
            .group_by(rows.c.b)
        ).all()
    }
    return income_by_bar, order_count_by_bar, expense_by_bar, customers_by_bar
