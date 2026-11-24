"""Time axis of the busiest-times reports: which slot a sale moment falls into and which slots the axis shows.

Hour and weekday slots repeat inside a range, so each slot carries how many real days fall into it;
averaging by that keeps a weekday that occurs five times comparable with one that occurs four times.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from web.management.reports.messages import MONTH_NAMES
from web.management.reports.menu.constants import UNIT_HOUR, UNIT_MINUTE, UNIT_MONTH, UNIT_WEEKDAY
from web.management.reports.menu.messages import WEEKDAY_NAMES

MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
MONTHS_PER_YEAR = 12


@dataclass(frozen=True)
class Moment:
    """When a sale happened as the database groups it: its business day and the WIB hour and minute of the sale."""

    day: date
    hour: int
    minute: int


@dataclass(frozen=True)
class TimeSlot:
    key: str
    label: str
    occurrences: int


def _weekday_index(day: date) -> int:
    """Sunday is 0; Python counts from Monday."""
    return (day.weekday() + 1) % DAYS_PER_WEEK


def slot_key(moment: Moment, unit: str) -> str:
    if unit == UNIT_MINUTE:
        return str(moment.minute)
    if unit == UNIT_HOUR:
        return str(moment.hour)
    if unit == UNIT_WEEKDAY:
        return str(_weekday_index(moment.day))
    if unit == UNIT_MONTH:
        return f"{moment.day.year:04d}-{moment.day.month:02d}"
    return moment.day.isoformat()


def _month_slots(start: date, end: date) -> list[TimeSlot]:
    result: list[TimeSlot] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        first = date(year, month, 1)
        last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        # A month cut by the range only counts the days inside it.
        days = (min(last, end) - max(first, start)).days + 1
        result.append(TimeSlot(f"{year:04d}-{month:02d}", f"{MONTH_NAMES[month - 1]} {year}", days))
        month += 1
        if month > MONTHS_PER_YEAR:
            month, year = 1, year + 1
    return result


def slots(start: date, end: date, unit: str, hour: int | None = None) -> list[TimeSlot]:
    """Every slot of the axis in order, empty ones included, since a quiet slot is a finding too."""
    days = (end - start).days + 1
    if unit == UNIT_MINUTE:
        parent = hour or 0
        return [TimeSlot(str(minute), f"{parent:02d}:{minute:02d}", days) for minute in range(MINUTES_PER_HOUR)]

    if unit == UNIT_HOUR:
        return [TimeSlot(str(value), f"{value:02d}:00", days) for value in range(HOURS_PER_DAY)]

    if unit == UNIT_WEEKDAY:
        counts = [0] * DAYS_PER_WEEK
        day = start
        while day <= end:
            counts[_weekday_index(day)] += 1
            day += timedelta(days=1)
        return [TimeSlot(str(index), WEEKDAY_NAMES[index], counts[index]) for index in range(DAYS_PER_WEEK)]

    if unit == UNIT_MONTH:
        return _month_slots(start, end)

    result = []
    day = start
    while day <= end:
        result.append(TimeSlot(day.isoformat(), f"{day.day} {MONTH_NAMES[day.month - 1]}", 1))
        day += timedelta(days=1)
    return result
