"""Leave requests decided by the manager: an approval marks the person on leave on every shift scheduled in the range."""
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.clock import now
from app.core.errors import DomainError
from app.models.attendance import PRESENT_STATUSES, Attendance, AttendanceStatus
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.user import User
from web.management.leave_requests import messages, repository
from web.management.leave_requests.constants import MAX_ATTENDANCE_NOTE_LENGTH, NOT_FOUND
from web.management.leave_requests.domain import Decision, LeaveFilter, LeavePage


def list_page(db: Session, filter: LeaveFilter, page: int, size: int) -> LeavePage:
    requests, total = repository.page_of(db, filter, page, size)
    return LeavePage(requests=requests, total=total, page=page, size=size)


def decide(db: Session, admin: User, request_id: str, decision: Decision) -> LeaveRequest:
    """A decision can be changed after a mis-tap: an approval is withdrawn first, then the new decision applies."""
    request = _owned(db, admin, request_id)
    if request.status == LeaveStatus.APPROVED:
        _withdraw_marks(db, request)

    request.status = LeaveStatus.APPROVED if decision.approve else LeaveStatus.REJECTED
    request.decided_by_id = admin.id
    request.decided_at = now()
    request.manager_note = (decision.note or "").strip() or None
    if decision.approve:
        _mark_leave(db, request)
    db.commit()
    db.refresh(request)
    return request


def delete(db: Session, admin: User, request_id: str) -> None:
    """A manager may delete any request of the branch; the leave marks of an approval go with it."""
    request = _owned(db, admin, request_id)
    if request.status == LeaveStatus.APPROVED:
        _withdraw_marks(db, request)
    path = request.attachment_path
    db.delete(request)
    db.commit()
    uploads.discard(db, path)


def _owned(db: Session, admin: User, request_id: str) -> LeaveRequest:
    request = repository.find(db, request_id)
    locked = admin.locked_outlet_id
    if request is None or (locked and request.outlet_id != locked):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return request


def _withdraw_marks(db: Session, request: LeaveRequest) -> None:
    for mark in repository.marks_made_by(db, request):
        db.delete(mark)
    db.flush()


def _mark_leave(db: Session, request: LeaveRequest) -> None:
    """A record already present or late is not overwritten: the person really came."""
    status = AttendanceStatus(request.type.value)
    for schedule in repository.schedules_in(db, request.user_id, request.start_date, request.end_date):
        record = repository.attendance_in_slot(db, schedule)
        if record is not None and record.status in PRESENT_STATUSES:
            continue
        if record is None:
            record = Attendance(
                outlet_id=schedule.outlet_id,
                user_id=request.user_id,
                date=schedule.date,
                shift_code_id=schedule.shift_code_id,
                schedule_id=schedule.id,
            )
            db.add(record)
        record.status = status
        record.clock_in_at = None
        record.clock_out_at = None
        record.note = request.reason[:MAX_ATTENDANCE_NOTE_LENGTH]
