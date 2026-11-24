"""What the summary service hands to the mappers."""
from dataclasses import dataclass
from datetime import date

from app.models.attendance import Attendance, AttendanceStatus


@dataclass(frozen=True)
class Day:
    date: date
    status: AttendanceStatus
    automatic: bool
    record: Attendance | None
    code: str | None
    role_name: str | None
    late_minutes: int
    work_minutes: int | None
    penalty: int


@dataclass(frozen=True)
class Totals:
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


@dataclass(frozen=True)
class Summary:
    month_start: date
    until: date
    totals: Totals
    days: list[Day]
