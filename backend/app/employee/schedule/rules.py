"""Checks shared by the schedule and day-off screens."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import protection
from app.core.clock import today
from app.core.errors import DomainError
from app.employee.schedule import messages
from app.employee.schedule.constants import DAYS_IN_WEEK, MAX_RANGE_DAYS
from app.models.day_off import DayOff
from app.models.user import User

NOT_FOUND = 404
CONFLICT = 409


def active_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise DomainError(messages.USER_NOT_FOUND, status=NOT_FOUND)
    if not user.is_active:
        raise DomainError(messages.USER_INACTIVE.format(username=user.username))
    protection.ensure_schedulable(user)
    return user


def ensure_not_day_off(db: Session, day: date, user_id: str) -> None:
    if db.scalar(select(DayOff.id).where(DayOff.date == day, DayOff.user_id == user_id)):
        raise DomainError(messages.ON_DAY_OFF, status=CONFLICT)


def week_range(start: date | None, end: date | None) -> tuple[date, date]:
    """A missing start is the Monday of the end's week (or this week), and a missing end is six days after the start."""
    if start is None:
        anchor = end or today()
        start = anchor - timedelta(days=anchor.weekday())
    if end is None:
        end = start + timedelta(days=DAYS_IN_WEEK - 1)
    if end < start:
        raise DomainError(messages.END_BEFORE_START)
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise DomainError(messages.RANGE_TOO_LONG.format(days=MAX_RANGE_DAYS))
    return date(start.year, start.month, start.day), date(end.year, end.month, end.day)
