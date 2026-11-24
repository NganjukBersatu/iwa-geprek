"""Turns the day plan into response schemas."""
from datetime import datetime

from app.core.clock import minutes_between
from app.employee.day_plan.domain import DayPlan, Segment
from app.employee.day_plan.schemas import DayPlanOut, SegmentOut


def segment_out(segment: Segment) -> SegmentOut:
    return SegmentOut(
        kind=segment.kind,
        starts_at=segment.starts_at,
        ends_at=segment.ends_at,
        minutes=minutes_between(segment.starts_at, segment.ends_at) or 0,
        code=segment.code,
        color=segment.color,
    )


def day_plan_out(plan: DayPlan, server_time: datetime) -> DayPlanOut:
    return DayPlanOut(
        server_time=server_time,
        segments=[segment_out(segment) for segment in plan.segments],
        scheduled_overtime=segment_out(plan.scheduled_overtime) if plan.scheduled_overtime else None,
    )
