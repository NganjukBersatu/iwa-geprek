"""Turns leave requests into response schemas."""
from app.core.http import static_url
from app.employee.leave.schemas import EmployeeLeaveRequestOut
from app.models.leave_request import LeaveRequest


def leave_out(request: LeaveRequest, base_url: str) -> EmployeeLeaveRequestOut:
    decider = request.decided_by
    return EmployeeLeaveRequestOut(
        id=request.id,
        type=request.type.value,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
        status=request.status.value,
        decided_by=(decider.name or decider.username) if decider else None,
        decided_at=request.decided_at,
        manager_note=request.manager_note,
        attachment_url=static_url(base_url, request.attachment_path),
        attachment_link=request.attachment_link,
        created_at=request.created_at,
    )
