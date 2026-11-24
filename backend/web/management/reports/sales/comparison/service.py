"""Builds the comparison: money of two ranges of business days, the earlier one cut at the same point when the range reaches today."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import day_opening
from app.core.money import ZERO, round_rupiah
from app.core.clock import WIB, now, today
from app.core.date_range import range_start
from app.core.errors import DomainError
from web.management.reports import messages as report_messages
from web.management.reports.common import TENTH, ensure_max_range
from web.management.reports.sales import messages
from web.management.reports.sales.comparison import repository
from web.management.reports.sales.comparison.domain import Comparison, ComparisonMode, Metric
from web.management.reports.sales.comparison.previous_range import previous_range


def _metric(current: Decimal, previous: Decimal) -> Metric:
    difference = current - previous
    change = (difference / previous * 100).quantize(TENTH) if previous else None
    return Metric(current=current, previous=previous, difference=difference, percent=change)


def _figures(db: Session, start: date, end: date, cut: datetime | None, outlet_id: str | None) -> dict[str, Decimal]:
    income, count = repository.income(db, start, end, cut, outlet_id)
    expense = repository.expense_total(db, start, end, cut, outlet_id)
    return {
        "income": income,
        "expense": expense,
        "transactions": Decimal(count),
        "average_transaction": round_rupiah(income / count) if count else ZERO,
        "customers": Decimal(repository.distinct_visitors(db, start, end, cut, outlet_id)),
        "profit": income - expense,
    }


def comparison(
    db: Session,
    start: date,
    end: date,
    mode: ComparisonMode,
    previous_start: date | None,
    previous_end: date | None,
    outlet_id: str | None,
) -> Comparison:
    """This range against its comparable earlier range; a range reaching today cuts both sides at the current time."""
    if end < start:
        raise DomainError(report_messages.END_BEFORE_START)
    ensure_max_range(start, end)

    previous_start, previous_end, label = previous_range(start, end, mode, previous_start, previous_end)

    cut_off_at = None
    previous_cut = None
    if end >= today():
        instant = now()
        cut_off_at = instant.astimezone(WIB).strftime("%H:%M")
        # A custom range of a different length is left whole; the person chose it.
        if mode != ComparisonMode.CUSTOM:
            # Both sides are measured from when their business day opened, so a session running past midnight is cut at the same point.
            opened = day_opening(db, start, outlet_id) or range_start(start)
            previous_opened = day_opening(db, previous_start, outlet_id) or range_start(previous_start)
            previous_cut = previous_opened + (instant - opened)
            label += messages.CUT_OFF_SUFFIX.format(time=cut_off_at.replace(":", "."))

    current = _figures(db, start, end, None, outlet_id)
    previous = _figures(db, previous_start, previous_end, previous_cut, outlet_id)
    return Comparison(
        start=start,
        end=end,
        mode=mode,
        previous_start=previous_start,
        previous_end=previous_end,
        comparison_label=label,
        cut_off_at=cut_off_at,
        **{key: _metric(current[key], previous[key]) for key in current},
    )
