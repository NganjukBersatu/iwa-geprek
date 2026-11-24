"""Builds the trend; figures and ordering match the legacy /laporan routes exactly."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.clock import today
from app.core.errors import DomainError
from app.core.money import RUPIAH
from web.management.reports.common import MAX_RANGE_DAYS, from_today
from web.management.reports.sales import messages
from web.management.reports.sales.trend import repository
from web.management.reports.sales.trend.bars import DEFAULT_POINTS, split_period, split_range
from web.management.reports.sales.trend.domain import Period, Trend, TrendPoint


def _bars(period: Period, count: int | None, start: date | None, end: date | None) -> tuple[Period, list]:
    """Either the last `count` units up to today, or a chosen range whose bar unit follows its length."""
    if start or end:
        start, end = from_today(start or end, end)
        if (end - start).days + 1 > MAX_RANGE_DAYS:
            raise DomainError(messages.TREND_RANGE_TOO_LONG.format(days=MAX_RANGE_DAYS))
        return split_range(start, end)
    return period, split_period(period, count or DEFAULT_POINTS[period], today())


def window(period: Period, count: int | None, start: date | None, end: date | None) -> tuple[Period, date, date]:
    """The days the dashboard covers, worked out without reading any figure."""
    used, bars = _bars(period, count, start, end)
    return used, bars[0].start, bars[-1].end


def trend(
    db: Session,
    period: Period,
    count: int | None,
    start: date | None,
    end: date | None,
    outlet_id: str | None,
) -> Trend:
    period, bars = _bars(period, count, start, end)
    income_by_bar, order_count_by_bar, expense_by_bar, customers_by_bar = repository.trend_figures(db, bars, outlet_id)
    points = []
    for i, bar in enumerate(bars):
        income = income_by_bar.get(i, Decimal("0"))
        expense = expense_by_bar.get(i, Decimal("0"))
        order_count = order_count_by_bar.get(i, 0)
        unique, returning = customers_by_bar.get(i, (0, 0))
        points.append(
            TrendPoint(
                label=bar.label,
                start=bar.start,
                end=bar.end,
                income=income,
                expense=expense,
                gross_profit=income - expense,
                order_count=order_count,
                average_transaction=(income / order_count).quantize(RUPIAH) if order_count else Decimal("0"),
                customers=unique,
                new_customers=unique - returning,
                returning_customers=returning,
            )
        )
    return Trend(period=period, start=bars[0].start, end=bars[-1].end, points=points)
