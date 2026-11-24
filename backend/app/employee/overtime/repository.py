"""Database reads for overtime."""
from datetime import date, datetime

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.models.attendance import PRESENT_STATUSES, Attendance
from app.models.overtime import Overtime
from app.models.schedule import Schedule
from app.models.user import User


def lock_user(db: Session, user_id: str) -> None:
    """Holds the person's row until the transaction ends, so two quick taps cannot both pass the checks."""
    db.execute(select(User.id).where(User.id == user_id).with_for_update())


def between(db: Session, user_ids: list[str], first: date, last: date) -> list[Overtime]:
    return list(
        db.scalars(
            select(Overtime)
            .where(Overtime.user_id.in_(user_ids), Overtime.date >= first, Overtime.date <= last)
            .order_by(Overtime.start_at.desc())
        ).all()
    )


def overlaps(db: Session, user_id: str, start: datetime, end: datetime) -> bool:
    """True when an entry of this person overlaps the range; an entry still running is open-ended."""
    return (
        db.scalar(
            select(Overtime.id)
            .where(
                Overtime.user_id == user_id,
                Overtime.start_at < end,
                or_(Overtime.end_at.is_(None), Overtime.end_at > start),
            )
            .limit(1)
        )
        is not None
    )


def schedules_on(db: Session, user_id: str, day: date) -> list[Schedule]:
    return list(db.scalars(select(Schedule).where(Schedule.user_id == user_id, Schedule.date == day)).all())


def worked_schedules(db: Session, user_ids: list[str], first: date, last: date) -> list[Schedule]:
    """Schedules of days the people were present on that same shift code."""
    present = exists().where(
        Attendance.user_id == Schedule.user_id,
        Attendance.date == Schedule.date,
        Attendance.shift_code_id == Schedule.shift_code_id,
        Attendance.status.in_(PRESENT_STATUSES),
    )
    return list(
        db.scalars(
            select(Schedule).where(
                Schedule.user_id.in_(user_ids), Schedule.date >= first, Schedule.date <= last, present
            )
        ).all()
    )
