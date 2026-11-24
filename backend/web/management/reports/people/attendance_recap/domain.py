"""What the attendance recap service hands to the mappers."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.models.attendance import AttendanceStatus


@dataclass(frozen=True)
class RecapDay:
    date: date
    code: str | None
    status: AttendanceStatus
    automatic: bool
    clock_in_at: datetime | None
    clock_out_at: datetime | None
    late_minutes: int
    work_minutes: int | None
    penalty: int
    note: str | None


@dataclass(frozen=True)
class RecapOvertime:
    id: str
    date: date
    start_at: datetime
    end_at: datetime
    minutes: int
    scheduled: bool
    note: str | None


@dataclass(frozen=True)
class UserRecap:
    user_id: str
    username: str
    name: str | None
    scheduled: int
    present: int
    late: int
    leave: int
    sick: int
    absent: int
    automatic_absences: int
    work_minutes: int
    late_minutes: int
    penalty: int
    overtime_minutes: int
    days: list[RecapDay]
    overtime: list[RecapOvertime]


@dataclass(frozen=True)
class RecapRule:
    late_tolerance_minutes: int
    late_penalty_per_minute: int


@dataclass(frozen=True)
class AttendanceRecap:
    start: date
    end: date
    rule: RecapRule
    total_penalty: int
    total_late_minutes: int
    total_overtime_minutes: int
    total_absent: int
    total_attended: int
    total_work_minutes: int
    total_revenue: Decimal
    # Omzet dibagi jam kerja tercatat; None bila belum ada jam kerja.
    revenue_per_work_hour: Decimal | None
    user: list[UserRecap]
