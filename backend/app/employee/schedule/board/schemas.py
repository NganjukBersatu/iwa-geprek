from datetime import date, datetime

from pydantic import BaseModel


class BoardAssignmentOut(BaseModel):
    id: str
    date: date
    user_id: str
    user_username: str
    user_name: str | None
    shift_code_id: str | None
    role_name: str | None
    note: str | None
    starts_at: datetime | None
    ends_at: datetime | None


class BoardDayOffOut(BaseModel):
    id: str
    date: date
    user_id: str
    user_username: str
    user_name: str | None
    shift_code_id: str | None
    note: str | None


class BoardShiftCodeOut(BaseModel):
    id: str
    code: str
    category: str | None
    start_clock: str | None
    end_clock: str | None
    overtime_start_clock: str | None
    overtime_end_clock: str | None
    color: str | None
    is_day_off: bool
    duration_minutes: int | None


class MonthBoardOut(BaseModel):
    month: str
    outlet_name: str | None
    assignments: list[BoardAssignmentOut]
    days_off: list[BoardDayOffOut]
    shift_codes: list[BoardShiftCodeOut]
