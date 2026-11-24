from datetime import date

from pydantic import BaseModel

from app.employee.performance.rating.schemas import RatingOut


class BucketOut(BaseModel):
    start: date
    end: date
    on_time_percent: int | None
    work_minutes: int
    overtime_minutes: int
    tasks_done: int


class CompositionOut(BaseModel):
    on_time: int
    late: int
    leave: int
    absent: int


class PerformanceOut(BaseModel):
    range: str
    start: date
    end: date
    counted_days: int
    buckets: list[BucketOut]
    composition: CompositionOut
    tasks_assigned: int
    tasks_done: int
    rating: RatingOut
