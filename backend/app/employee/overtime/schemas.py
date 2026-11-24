from datetime import date, datetime

from pydantic import BaseModel, Field

from app.employee.overtime.constants import NOTE_MAX_LENGTH


class UnplannedOvertimeIn(BaseModel):
    started_at: datetime
    ended_at: datetime
    note: str = Field(min_length=1, max_length=NOTE_MAX_LENGTH)


class OvertimeOut(BaseModel):
    id: str
    date: date
    started_at: datetime
    ended_at: datetime
    minutes: int
    scheduled: bool
    note: str | None
