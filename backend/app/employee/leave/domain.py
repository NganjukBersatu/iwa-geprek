"""What the routes hand to the leave service."""
from dataclasses import dataclass
from datetime import date

from app.models.leave_request import LeaveType


@dataclass(frozen=True)
class LeaveForm:
    type: LeaveType
    start_date: date
    end_date: date
    reason: str
    link: str | None
