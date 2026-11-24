"""A schedule the employee makes when they have none today; after it, the clock-in is the ordinary one."""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.clock import local_date
from app.core.errors import DomainError
from app.employee.attendance import messages
from app.employee.attendance.self_schedule import repository
from app.employee.attendance.self_schedule.domain import Options, Suggestion
from app.employee.schedule.assignment import Window, work_window
from app.employee.schedule.constants import SELF_SCHEDULE_RANGE_MINUTES
from app.employee.schedule.lookup import around, nearby_days
from app.models.outlet import Outlet
from app.models.role import Role
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode
from app.models.user import User

NOT_FOUND = 404
RANGE = timedelta(minutes=SELF_SCHEDULE_RANGE_MINUTES)


def _windows(db: Session, user: User, at: datetime) -> list[Window]:
    """The hour ranges of the person's nearby assignments, read with the same rule as everywhere else."""
    found = [work_window(item.date, item, item.shift_code) for item in around(db, user.id, at)]
    return [window for window in found if window is not None]


def _free(suggestion: Suggestion, windows: list[Window]) -> bool:
    return all(not (suggestion.starts_at < end and start < suggestion.ends_at) for start, end in windows)


def can_make(db: Session, user: User, at: datetime) -> bool:
    """Not on a day off, and no assignment's range holds the instant."""
    if repository.has_day_off_on(db, user.id, local_date(at)):
        return False
    return all(not (start <= at <= end) for start, end in _windows(db, user, at))


def _near(code: ShiftCode, at: datetime) -> Suggestion | None:
    """The code placed on each nearby date, as an assignment would be, kept when its start is within range of now."""
    for day in nearby_days(at):
        window = work_window(day, None, code)
        if window is not None and abs(window[0] - at) <= RANGE:
            return Suggestion(code, day, window[0], window[1])
    return None


def suggestions(db: Session, user: User, outlet_id: str, at: datetime) -> list[Suggestion]:
    """Codes starting within range of now whose range does not cross another assignment of the person."""
    windows = _windows(db, user, at)
    found = [_near(code, at) for code in repository.working_codes(db, outlet_id)]
    return sorted((item for item in found if item is not None and _free(item, windows)), key=lambda item: item.starts_at)


def options(db: Session, user: User, outlet_id: str | None, at: datetime) -> Options:
    """Suggestions need a branch; without one only the branches and roles are listed."""
    return Options(
        outlets=repository.outlets(db),
        roles=repository.worker_roles(db),
        suggestions=suggestions(db, user, outlet_id, at) if outlet_id else [],
    )


def create(
    db: Session, user: User, outlet_id: str, role_id: str, shift_code_id: str, reason: str | None, at: datetime
) -> Schedule:
    """Every choice is checked again here, since the options on the screen may be old."""
    repository.lock_user(db, user.id)
    if not can_make(db, user, at):
        raise DomainError(messages.SELF_SCHEDULE_EXISTS)

    outlet = db.get(Outlet, outlet_id)
    role = db.get(Role, role_id)
    code = db.get(ShiftCode, shift_code_id)
    if outlet is None or role is None or role.is_admin or code is None or code.outlet_id != outlet.id or code.is_day_off:
        raise DomainError(messages.SELF_SCHEDULE_NOT_FOUND, status=NOT_FOUND)

    suggestion = _near(code, at)
    if suggestion is None:
        raise DomainError(messages.SELF_SCHEDULE_OUT_OF_RANGE)
    if not _free(suggestion, _windows(db, user, at)):
        raise DomainError(messages.SELF_SCHEDULE_OVERLAP)

    schedule = Schedule(
        id=str(uuid.uuid4()),
        outlet_id=outlet.id,
        date=suggestion.day,
        user_id=user.id,
        shift_code_id=code.id,
        starts_at=suggestion.starts_at,
        ends_at=suggestion.ends_at,
        role_id=role.id,
        note=(reason or "").strip() or None,
    )
    db.add(schedule)
    db.flush()
    return schedule
