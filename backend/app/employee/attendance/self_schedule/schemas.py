from datetime import date, datetime

from pydantic import BaseModel, Field

from app.employee.attendance.constants import MAX_ID_LENGTH, MAX_NOTE_LENGTH


class SelfScheduleChoiceOut(BaseModel):
    id: str
    name: str


class SuggestionOut(BaseModel):
    shift_code_id: str
    code: str
    color: str | None
    date: date
    starts_at: datetime
    ends_at: datetime


class SelfScheduleOptionsOut(BaseModel):
    outlets: list[SelfScheduleChoiceOut]
    roles: list[SelfScheduleChoiceOut]
    suggestions: list[SuggestionOut]


class SelfScheduleIn(BaseModel):
    outlet_id: str = Field(max_length=MAX_ID_LENGTH)
    role_id: str = Field(max_length=MAX_ID_LENGTH)
    shift_code_id: str = Field(max_length=MAX_ID_LENGTH)
    reason: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
