from datetime import datetime

from pydantic import BaseModel

from app.employee.day_plan.domain import SegmentKind


class SegmentOut(BaseModel):
    kind: SegmentKind
    starts_at: datetime
    ends_at: datetime
    minutes: int
    code: str | None
    color: str | None


class DayPlanOut(BaseModel):
    server_time: datetime
    segments: list[SegmentOut]
    scheduled_overtime: SegmentOut | None
