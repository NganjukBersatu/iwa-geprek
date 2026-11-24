"""What the performance service hands to the mappers."""
import enum
from dataclasses import dataclass
from datetime import date

from app.employee.performance.rating.domain import Rating


class Range(str, enum.Enum):
    CYCLE = "cycle"
    PREVIOUS = "previous"
    ALL = "all"


@dataclass(frozen=True)
class Bucket:
    """One bar of the charts: a week counted from the first day of the cycle, or a whole cycle for the all range."""

    start: date
    end: date
    on_time_percent: int | None
    work_minutes: int
    overtime_minutes: int
    tasks_done: int


@dataclass(frozen=True)
class Composition:
    on_time: int
    late: int
    leave: int
    absent: int


@dataclass(frozen=True)
class Performance:
    range: Range
    start: date
    end: date
    counted_days: int
    buckets: list[Bucket]
    composition: Composition
    tasks_assigned: int
    tasks_done: int
    rating: Rating
