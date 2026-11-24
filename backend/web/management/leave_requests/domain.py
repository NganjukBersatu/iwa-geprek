"""What the leave request service receives from the routes and hands to the mappers."""
from dataclasses import dataclass, field

from app.models.leave_request import LeaveRequest, LeaveStatus


@dataclass(frozen=True)
class LeaveFilter:
    status: LeaveStatus | None = LeaveStatus.PENDING
    search: str | None = None
    outlet_id: str | None = None


@dataclass(frozen=True)
class Decision:
    approve: bool
    note: str | None = None


@dataclass(frozen=True)
class LeavePage:
    requests: list[LeaveRequest] = field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20
