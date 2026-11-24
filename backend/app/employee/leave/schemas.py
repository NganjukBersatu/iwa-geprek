from datetime import date, datetime

from pydantic import BaseModel


class EmployeeLeaveRequestOut(BaseModel):
    id: str
    type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    decided_by: str | None
    decided_at: datetime | None
    manager_note: str | None
    attachment_url: str | None
    attachment_link: str | None
    created_at: datetime
