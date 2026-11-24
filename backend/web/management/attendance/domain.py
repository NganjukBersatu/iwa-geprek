"""What the attendance service receives from the routes and hands to the mappers."""
from dataclasses import dataclass, field
from datetime import date, datetime

from app.models.attendance import Attendance, AttendanceStatus
from app.models.attendance_clock_event import AttendanceClockEvent
from app.models.user import User


@dataclass(frozen=True)
class AttendanceFilter:
    """[start] and [end] may carry a clock time; then a record counts when its worked hours overlap the range."""

    start: date | None = None
    end: date | None = None
    user_id: str | None = None
    status: AttendanceStatus | None = None
    has_photo: bool | None = None
    outside_schedule: bool | None = None
    search: str | None = None
    outlet_id: str | None = None


@dataclass(frozen=True)
class MarkDraft:
    user_id: str
    date: date
    shift_code_id: str | None
    status: AttendanceStatus
    schedule_id: str | None = None
    note: str | None = None
    clock_in_at: datetime | None = None
    clock_out_at: datetime | None = None


@dataclass(frozen=True)
class AttendanceChanges:
    """A value sent as None clears the clock or note; [given] names the fields that were sent at all."""

    given: frozenset[str]
    status: AttendanceStatus | None = None
    clock_in_at: datetime | None = None
    clock_out_at: datetime | None = None
    note: str | None = None


@dataclass(frozen=True)
class AttendanceEntry:
    record: Attendance
    user: User
    shift_code: str | None
    shift_code_color: str | None
    branch_latitude: float | None
    branch_longitude: float | None
    late_minutes: int
    penalty: int
    work_minutes: int | None
    # Kejadian pengiriman absen ini dari app, dari yang paling dulu diterima; kosong untuk absen yang dicatat admin.
    events: tuple[AttendanceClockEvent, ...] = ()


@dataclass(frozen=True)
class AttendancePage:
    entries: list[AttendanceEntry] = field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20
