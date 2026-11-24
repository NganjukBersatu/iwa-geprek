from datetime import date, datetime

from pydantic import BaseModel


class ScheduleSummary(BaseModel):
    id: str
    date: date
    code: str | None
    color: str | None
    starts_at: datetime | None
    ends_at: datetime | None


class EmployeeAttendanceOut(BaseModel):
    id: str
    date: date
    status: str
    clock_in_at: datetime | None
    clock_out_at: datetime | None
    auto_closed: bool
    clock_in_photo_url: str | None
    clock_out_photo_url: str | None
    schedule: ScheduleSummary | None
    work_minutes: int | None


class AutoCloseNotice(BaseModel):
    id: str
    date: date
    code: str | None
    clock_in_at: datetime | None
    clock_out_at: datetime | None


class ClockInBlockOut(BaseModel):
    """`at` is when the clock-in opens (not_open_yet) or when the assignment ended (ended)."""

    reason: str
    schedule: ScheduleSummary | None
    at: datetime | None


class AttendanceBranchOut(BaseModel):
    """The branch the next clock-in or clock-out is judged against; a point or radius that is unset is not judged."""

    id: str
    name: str
    latitude: float | None
    longitude: float | None
    radius_meters: int | None


class AttendanceStateOut(BaseModel):
    date: date
    server_time: datetime
    can_clock_in: bool
    can_clock_out: bool
    attendance: EmployeeAttendanceOut | None
    schedule: ScheduleSummary | None
    auto_close_notices: list[AutoCloseNotice]
    clock_in_block: ClockInBlockOut | None
    # True when the person has no assignment today, so the clock-in starts by making one.
    can_self_schedule: bool
    branch: AttendanceBranchOut | None
