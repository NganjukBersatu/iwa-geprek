"""Database reads and small writes for the admin's leave request screen."""
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.attendance import Attendance, AttendanceStatus
from app.models.leave_request import LeaveRequest
from app.models.schedule import Schedule
from app.models.user import User
from web.management.leave_requests.domain import LeaveFilter


def _conditions(filter: LeaveFilter) -> list:
    conditions = []
    if filter.outlet_id:
        conditions.append(LeaveRequest.outlet_id == filter.outlet_id)
    if filter.status:
        conditions.append(LeaveRequest.status == filter.status)
    if filter.search:
        by_person = select(User.id).where(or_(contains(User.username, filter.search), contains(User.name, filter.search)))
        conditions.append(or_(LeaveRequest.user_id.in_(by_person), contains(LeaveRequest.reason, filter.search)))
    return conditions


def page_of(db: Session, filter: LeaveFilter, page: int, size: int) -> tuple[list[LeaveRequest], int]:
    conditions = _conditions(filter)
    total = db.scalar(select(func.count()).select_from(LeaveRequest).where(*conditions)) or 0
    rows = db.scalars(
        select(LeaveRequest)
        .where(*conditions)
        .order_by(LeaveRequest.start_date, LeaveRequest.created_at, LeaveRequest.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(rows), total


def find(db: Session, request_id: str) -> LeaveRequest | None:
    return db.get(LeaveRequest, request_id)


def user_by_id(db: Session, ids: set[str]) -> dict[str, User]:
    if not ids:
        return {}
    return {user.id: user for user in db.scalars(select(User).where(User.id.in_(ids))).all()}


def marks_made_by(db: Session, request: LeaveRequest) -> list[Attendance]:
    """Leave marks still exactly as the approval left them: same status and no clock-in; ones an admin corrected stay out."""
    return list(
        db.scalars(
            select(Attendance).where(
                Attendance.user_id == request.user_id,
                Attendance.date >= request.start_date,
                Attendance.date <= request.end_date,
                Attendance.status == AttendanceStatus(request.type.value),
                Attendance.clock_in_at.is_(None),
            )
        ).all()
    )


def schedules_in(db: Session, user_id: str, start: date, end: date) -> list[Schedule]:
    return list(db.scalars(select(Schedule).where(Schedule.user_id == user_id, Schedule.date >= start, Schedule.date <= end)).all())


def attendance_in_slot(db: Session, schedule: Schedule) -> Attendance | None:
    return db.scalar(
        select(Attendance).where(
            Attendance.date == schedule.date,
            Attendance.shift_code_id == schedule.shift_code_id,
            Attendance.user_id == schedule.user_id,
        )
    )
