from datetime import date, datetime

from pydantic import BaseModel


class LocationOut(BaseModel):
    mode: str | None
    note: str | None
    distance_meters: float | None
    accuracy_meters: float | None
    radius_meters: int | None


class DayOut(BaseModel):
    date: date
    status: str
    automatic: bool
    shift_code: str | None
    role_name: str | None
    clock_in_at: datetime | None
    clock_out_at: datetime | None
    late_minutes: int
    work_minutes: int | None
    penalty: int
    note: str | None
    outside_schedule_reason: str | None
    auto_closed: bool
    clock_in_photo_url: str | None
    clock_out_photo_url: str | None
    clock_in_location: LocationOut | None
    clock_out_location: LocationOut | None


class TotalsOut(BaseModel):
    scheduled: int
    present: int
    late: int
    leave: int
    sick: int
    absent: int
    work_minutes: int
    late_minutes: int
    overtime_minutes: int
    penalty: int


class AttendanceSummaryOut(BaseModel):
    month: str
    until: date
    totals: TotalsOut
    days: list[DayOut]
