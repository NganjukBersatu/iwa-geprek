"""Turns leave requests into response schemas."""
from app.core.http import static_url
from app.models.leave_request import LeaveRequest
from app.models.user import User
from web.management.leave_requests.domain import LeavePage
from web.management.leave_requests.schemas import LeaveRequestOut, LeaveRequestPageOut

NO_ROLE = "-"


def leave_request_out(request: LeaveRequest, user: User, base_url: str) -> LeaveRequestOut:
    decider = request.decided_by
    return LeaveRequestOut(
        id=request.id,
        user_id=request.user_id,
        username=user.username,
        name=user.name,
        role_name=user.role.name if user.role else NO_ROLE,
        type=request.type,
        start_date=request.start_date,
        end_date=request.end_date,
        reason=request.reason,
        status=request.status,
        decided_by=(decider.name or decider.username) if decider else None,
        decided_at=request.decided_at,
        manager_note=request.manager_note,
        attachment_url=static_url(base_url, request.attachment_path),
        attachment_link=request.attachment_link,
        created_at=request.created_at,
    )


def leave_request_page_out(page: LeavePage, user: dict[str, User], base_url: str) -> LeaveRequestPageOut:
    return LeaveRequestPageOut(
        items=[leave_request_out(request, user[request.user_id], base_url) for request in page.requests if request.user_id in user],
        total=page.total,
        page=page.page,
        size=page.size,
    )
