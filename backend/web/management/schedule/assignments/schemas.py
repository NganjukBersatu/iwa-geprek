import datetime as dt

from pydantic import BaseModel, Field

from app.employee.schedule.constants import MAX_NOTE_LENGTH


class AssignmentCreateIn(BaseModel):
    date: dt.date
    user_id: str
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    shift_code_id: str | None = None
    role_id: str | None = Field(None, description="The day's role label on the board; it grants no permission")


class AssignmentUpdateIn(BaseModel):
    """A field left out stays; a code or role sent empty is released."""

    date: dt.date | None = None
    user_id: str | None = None
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    shift_code_id: str | None = None
    role_id: str | None = None


class AssignmentSwapIn(BaseModel):
    first_id: str
    second_id: str


class AssignmentOut(BaseModel):
    id: str
    date: dt.date
    user_id: str
    user_username: str
    note: str | None
    shift_code_id: str | None
    role_id: str | None
    role_name: str | None
    created_at: dt.datetime
    updated_at: dt.datetime


class AssignmentSwapOut(BaseModel):
    first: AssignmentOut
    second: AssignmentOut
