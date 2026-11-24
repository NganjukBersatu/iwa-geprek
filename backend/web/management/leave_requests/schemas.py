from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.leave_request import LeaveStatus, LeaveType
from web.management.leave_requests.constants import MAX_NOTE_LENGTH


class DecisionIn(BaseModel):
    approve: bool
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class LeaveRequestOut(BaseModel):
    id: str
    user_id: str
    username: str
    name: str | None
    role_name: str
    type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus
    decided_by: str | None
    decided_at: datetime | None
    manager_note: str | None
    attachment_url: str | None
    attachment_link: str | None
    created_at: datetime


class LeaveRequestPageOut(BaseModel):
    items: list[LeaveRequestOut]
    total: int = Field(description="Every request matching the filter, not only this page")
    page: int
    size: int
