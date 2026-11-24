"""Collects today's segments; a segment of yesterday still counts while it has not ended."""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.clock import as_aware, local_date
from app.employee.day_plan import repository
from app.employee.day_plan.domain import DayPlan, Segment, SegmentKind
from app.employee.schedule.assignment import overtime_window, work_window
from app.models.user import User


def _relevant(day: date, ends_at: datetime, today: date, instant: datetime) -> bool:
    return day == today or ends_at > instant


def build(db: Session, user: User, instant: datetime) -> DayPlan:
    today = local_date(instant)
    segments: list[Segment] = []
    scheduled_overtime: Segment | None = None

    for schedule in repository.schedules_around(db, user.id, today):
        code = schedule.shift_code
        work = work_window(schedule.date, schedule, code)
        if work is not None and _relevant(schedule.date, work[1], today, instant):
            segments.append(
                Segment(SegmentKind.WORK, work[0], work[1], code.code if code else None, code.color if code else None)
            )
        overtime = overtime_window(schedule)
        if overtime is not None:
            segment = Segment(SegmentKind.SCHEDULED_OVERTIME, overtime[0], overtime[1])
            if schedule.date == today:
                scheduled_overtime = segment
            if _relevant(schedule.date, overtime[1], today, instant):
                segments.append(segment)

    for item in repository.unplanned_around(db, user.id, today):
        if item.end_at is None:
            continue
        end_at = as_aware(item.end_at)
        if _relevant(item.date, end_at, today, instant):
            segments.append(Segment(SegmentKind.UNPLANNED_OVERTIME, as_aware(item.start_at), end_at))

    segments.sort(key=lambda segment: segment.starts_at)
    return DayPlan(segments=segments, scheduled_overtime=scheduled_overtime)
