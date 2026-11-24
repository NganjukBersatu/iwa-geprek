from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SegmentKind(str, Enum):
    WORK = "work"
    SCHEDULED_OVERTIME = "scheduled_overtime"
    UNPLANNED_OVERTIME = "unplanned_overtime"


@dataclass(frozen=True)
class Segment:
    kind: SegmentKind
    starts_at: datetime
    ends_at: datetime
    code: str | None = None
    color: str | None = None


@dataclass(frozen=True)
class DayPlan:
    segments: list[Segment]
    scheduled_overtime: Segment | None
