"""Pure time math for assignments, with no database and no clock."""
from datetime import date, datetime, time, timedelta, timezone

from app.core.clock import WIB
from app.employee.schedule.constants import MINUTES_PER_DAY, MINUTES_PER_HOUR


def _clock_to_minutes(clock: str) -> int:
    hours, minutes = clock.split(":")
    return int(hours) * MINUTES_PER_HOUR + int(minutes)


def clock_minutes(clock: str) -> int:
    """Menit sejak 00.00 apa adanya; 24:00 bernilai 1440, tidak diputar ke 0."""
    return _clock_to_minutes(clock)


def minutes_of_day(clock: str) -> int:
    """Menit sejak 00.00; 24:00 sama dengan 00:00 di hari berikutnya."""
    return _clock_to_minutes(clock) % MINUTES_PER_DAY


def duration_minutes(start_clock: str | None, end_clock: str | None) -> int | None:
    """An end clock equal to or before the start clock falls on the next day."""
    if not start_clock or not end_clock:
        return None
    difference = (_clock_to_minutes(end_clock) - _clock_to_minutes(start_clock)) % MINUTES_PER_DAY
    return difference or MINUTES_PER_DAY


def window(day: date, start_clock: str | None, minutes: int | None) -> tuple[datetime, datetime] | None:
    """Start and end instants in UTC for an assignment on that day."""
    if not start_clock or not minutes:
        return None
    midnight = datetime.combine(day, time.min, tzinfo=WIB)
    start = (midnight + timedelta(minutes=_clock_to_minutes(start_clock))).astimezone(timezone.utc)
    return start, start + timedelta(minutes=minutes)


def window_from_code(
    day: date, start_clock: str | None, end_clock: str | None, stored_minutes: int | None = None
) -> tuple[datetime, datetime] | None:
    """Uses the stored duration when the code has one and derives it from the clocks otherwise."""
    return window(day, start_clock, stored_minutes or duration_minutes(start_clock, end_clock))
