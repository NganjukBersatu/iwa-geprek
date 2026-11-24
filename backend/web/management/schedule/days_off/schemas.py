import datetime as dt

from pydantic import BaseModel, Field

from app.employee.schedule.constants import MAX_NOTE_LENGTH


class DayOffCreateIn(BaseModel):
    date: dt.date
    user_id: str
    shift_code_id: str | None = Field(None, description="Only a code marked as a day off")
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class DayOffOut(BaseModel):
    id: str
    date: dt.date
    user_id: str
    user_username: str
    shift_code_id: str | None
    note: str | None
