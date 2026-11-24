"""Cuts a period or a chosen range into the bars of the trend chart."""
from datetime import date, timedelta

from web.management.reports.messages import DAY_NAMES, MONTH_NAMES
from web.management.reports.sales.periods import month_end, months_back
from web.management.reports.sales.trend.constants import DAYS_PER_WEEK, MAX_DAYS_DAILY_BARS, MAX_DAYS_WEEKLY_BARS
from web.management.reports.sales.trend.domain import Bar, Period

# Bars drawn when the caller gives no count: a week, a month, and most of a year.
DEFAULT_POINTS = {Period.DAILY: 7, Period.WEEKLY: 4, Period.MONTHLY: 8}


def _range_label(start: date, end: date) -> str:
    if start.month == end.month:
        return f"{start.day}-{end.day} {MONTH_NAMES[end.month - 1]}"
    return f"{start.day} {MONTH_NAMES[start.month - 1]}-{end.day} {MONTH_NAMES[end.month - 1]}"


def split_period(period: Period, count: int, anchor: date) -> list[Bar]:
    """The last `count` units up to `anchor`, newest on the right; the running week or month may be partial."""
    if period == Period.DAILY:
        return [
            Bar(DAY_NAMES[day.weekday()], day, day)
            for day in (anchor - timedelta(days=n) for n in reversed(range(count)))
        ]

    if period == Period.WEEKLY:
        this_monday = anchor - timedelta(days=anchor.weekday())
        bars = []
        for n in reversed(range(count)):
            start = this_monday - timedelta(weeks=n)
            full_end = start + timedelta(days=DAYS_PER_WEEK - 1)
            bars.append(Bar(_range_label(start, full_end), start, min(full_end, anchor)))
        return bars

    bars = []
    for n in reversed(range(count)):
        start = months_back(anchor, n)
        bars.append(Bar(MONTH_NAMES[start.month - 1], start, min(month_end(start), anchor)))
    return bars


def split_range(start: date, end: date) -> tuple[Period, list[Bar]]:
    """A chosen range cut into bars whose unit follows its length; weeks count from the chosen start, not Monday."""
    days = (end - start).days + 1

    if days <= MAX_DAYS_DAILY_BARS:
        return Period.DAILY, [
            Bar(f"{day.day} {MONTH_NAMES[day.month - 1]}", day, day)
            for day in (start + timedelta(days=n) for n in range(days))
        ]

    if days <= MAX_DAYS_WEEKLY_BARS:
        bars = []
        first = start
        while first <= end:
            last = min(first + timedelta(days=DAYS_PER_WEEK - 1), end)
            bars.append(Bar(_range_label(first, last), first, last))
            first = last + timedelta(days=1)
        return Period.WEEKLY, bars

    crosses_year = start.year != end.year
    bars = []
    first = start
    while first <= end:
        last_of_month = month_end(first)
        label = MONTH_NAMES[first.month - 1]
        if crosses_year:
            label = f"{label} {first.year % 100:02d}"
        bars.append(Bar(label, first, min(last_of_month, end)))
        first = last_of_month + timedelta(days=1)
    return Period.MONTHLY, bars
