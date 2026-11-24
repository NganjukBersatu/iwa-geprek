from datetime import datetime

from pydantic import BaseModel

from app.employee.activity.domain import Action, Group


class EventOut(BaseModel):
    id: str
    group: Group
    action: Action
    at: datetime
    subject: str | None
    status: str | None
    minutes: int | None


class ActivityPageOut(BaseModel):
    events: list[EventOut]
    next_before: datetime | None
