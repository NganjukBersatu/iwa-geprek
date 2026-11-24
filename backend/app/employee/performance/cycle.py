"""A pay cycle starts on the day of the month the person joined and ends the day before the next such day."""
import calendar
from datetime import date, timedelta


def _start_in(year: int, month: int, anchor_day: int) -> date:
    """The anchor day of that month; a month too short for it uses its last day."""
    return date(year, month, min(anchor_day, calendar.monthrange(year, month)[1]))


def _shift_month(year: int, month: int, step: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + step
    return index // 12, index % 12 + 1


def containing(anchor_day: int, day: date) -> tuple[date, date]:
    """First and last day of the cycle that holds [day]."""
    start = _start_in(day.year, day.month, anchor_day)
    if start > day:
        start = _start_in(*_shift_month(day.year, day.month, -1), anchor_day)
    next_start = _start_in(*_shift_month(start.year, start.month, 1), anchor_day)
    return start, next_start - timedelta(days=1)


def previous(anchor_day: int, day: date) -> tuple[date, date]:
    start, _ = containing(anchor_day, day)
    return containing(anchor_day, start - timedelta(days=1))
