"""Date bounds of report filters: a WIB date, optionally narrowed to a minute, turned into UTC instants."""
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated

from pydantic import PlainValidator

from app.core.clock import WIB

_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}:\d{2}))?$")
FORMAT_ERROR = "Format tanggal harus YYYY-MM-DD atau YYYY-MM-DDTHH:MM"
DAY_FORMAT_ERROR = "Format tanggal harus YYYY-MM-DD"


class DayBound(date):
    """A date that may carry a clock time; arithmetic with timedelta keeps the time, so a shifted comparison period keeps it too."""

    clock: time | None

    def __new__(cls, year: int, month: int, day: int, clock: time | None = None):
        bound = super().__new__(cls, year, month, day)
        bound.clock = clock
        return bound

    def _keep_clock(self, result: date) -> "DayBound":
        return DayBound(result.year, result.month, result.day, self.clock)

    def __add__(self, other):
        result = date.__add__(self, other)
        return self._keep_clock(result) if isinstance(other, timedelta) else result

    __radd__ = __add__

    def __sub__(self, other):
        result = date.__sub__(self, other)
        return self._keep_clock(result) if isinstance(other, timedelta) else result

    def plain(self) -> date:
        return date(self.year, self.month, self.day)


def parse_bound(value) -> date:
    """Reads `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM` as a DayBound."""
    if isinstance(value, DayBound):
        return value
    if isinstance(value, datetime):
        return DayBound(value.year, value.month, value.day, value.time().replace(second=0, microsecond=0))
    if isinstance(value, date):
        return DayBound(value.year, value.month, value.day)
    match = _PATTERN.match(str(value).strip())
    if not match:
        raise ValueError(FORMAT_ERROR)
    day = date.fromisoformat(match.group(1))
    clock = time.fromisoformat(match.group(2)) if match.group(2) else None
    return DayBound(day.year, day.month, day.day, clock)


# Query parameter type of a range filter on instants, such as clock-in times.
Bound = Annotated[date, PlainValidator(parse_bound, json_schema_input_type=str)]


def parse_day(value) -> date:
    """Reads `YYYY-MM-DD` only: a business day has no clock time."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return date(value.year, value.month, value.day)
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as error:
        raise ValueError(DAY_FORMAT_ERROR) from error


# Query parameter type of every range filter on money and stock, which are filtered by their stored business day.
Day = Annotated[date, PlainValidator(parse_day, json_schema_input_type=str)]


def range_start(day: date) -> datetime:
    """Inclusive UTC lower bound: 00:00 WIB of the day, or the clock time it carries."""
    clock = getattr(day, "clock", None)
    return datetime.combine(date(day.year, day.month, day.day), clock or time.min, tzinfo=WIB).astimezone(timezone.utc)


def range_end(day: date) -> datetime:
    """Exclusive UTC upper bound: 00:00 WIB of the next day, or the end of the minute it carries."""
    if getattr(day, "clock", None) is not None:
        return range_start(day) + timedelta(minutes=1)
    return range_start(date(day.year, day.month, day.day) + timedelta(days=1))
