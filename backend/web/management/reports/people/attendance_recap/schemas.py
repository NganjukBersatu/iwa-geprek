from datetime import date, datetime
from decimal import Decimal

from app.models.attendance import AttendanceStatus
from web.management.reports.sales.response import ResponseModel


class RecapDayOut(ResponseModel):
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


class RecapOvertimeOut(ResponseModel):
    id: str
    date: date
    start_at: datetime
    end_at: datetime
    minutes: int
    scheduled: bool
    note: str | None


class UserRecapOut(ResponseModel):
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
    days: list[RecapDayOut]
    overtime: list[RecapOvertimeOut]


class RecapRuleOut(ResponseModel):
    late_tolerance_minutes: int
    late_penalty_per_minute: int


class AttendanceRecapOut(ResponseModel):
    start: date
    end: date
    rule: RecapRuleOut
    total_penalty: int
    total_late_minutes: int
    total_overtime_minutes: int
    total_absent: int
    total_attended: int
    total_work_minutes: int
    total_revenue: Decimal
    revenue_per_work_hour: Decimal | None
    user: list[UserRecapOut]
