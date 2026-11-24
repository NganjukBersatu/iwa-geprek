"""Chooses the earlier range a comparison is made against, and its label."""
from datetime import date, timedelta

from app.core.clock import today
from app.core.errors import DomainError
from web.management.reports.sales import messages
from web.management.reports.sales.comparison.domain import ComparisonMode
from web.management.reports.sales.constants import MONTHS_PER_YEAR
from web.management.reports.sales.periods import month_end, months_back, same_day_months_back


def _custom_label(previous_start: date, previous_end: date) -> str:
    if previous_end != previous_start:
        return messages.VS_CUSTOM_RANGE.format(start=previous_start, end=previous_end)
    return messages.VS_CUSTOM_DAY.format(start=previous_start)


def previous_range(start: date, end: date, mode: ComparisonMode, previous_start, previous_end) -> tuple:
    """The comparable earlier range and its label: whole months against whole months, otherwise the same length."""
    length = (end - start).days + 1
    if mode == ComparisonMode.CUSTOM:
        if not previous_start or not previous_end:
            raise DomainError(messages.CUSTOM_NEEDS_PREVIOUS)
        if previous_end < previous_start:
            raise DomainError(messages.PREVIOUS_RANGE_REVERSED)
        return previous_start, previous_end, _custom_label(previous_start, previous_end)
    if mode == ComparisonMode.WEEK:
        return start - timedelta(days=7), end - timedelta(days=7), messages.VS_LAST_WEEK
    if mode == ComparisonMode.MONTH:
        return same_day_months_back(start, 1), same_day_months_back(end, 1), messages.VS_LAST_MONTH_SAME_DATE
    if mode == ComparisonMode.YEAR:
        return (
            same_day_months_back(start, MONTHS_PER_YEAR),
            same_day_months_back(end, MONTHS_PER_YEAR),
            messages.VS_LAST_YEAR,
        )

    if start.day == 1 and end == month_end(end):
        months = (end.year - start.year) * MONTHS_PER_YEAR + (end.month - start.month) + 1
        label = messages.VS_LAST_MONTH if months == 1 else messages.VS_MONTHS_BEFORE.format(months=months)
        return months_back(start, months), start - timedelta(days=1), label

    previous_end = start - timedelta(days=1)
    if length == 1:
        label = messages.VS_YESTERDAY if end == today() else messages.VS_DAY_BEFORE
    else:
        label = messages.VS_DAYS_BEFORE.format(days=length)
    return previous_end - timedelta(days=length - 1), previous_end, label
