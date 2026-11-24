"""Queries for the assignments open to a clock-in at a given instant."""
from datetime import date, datetime, timedelta

from sqlalchemy import ColumnElement, select, update
from sqlalchemy.orm import Session

from app.core.clock import as_aware, local_date
from app.employee.schedule.constants import CLOCK_IN_EARLY_MINUTES, LOOKBACK_DAYS
from app.models.schedule import Schedule


def nearby_days(at: datetime) -> list[date]:
    """The dates an assignment touching the instant can carry: a running one started at most a day before, a coming one starts by tomorrow."""
    today = local_date(at)
    return [today + timedelta(days=offset) for offset in range(-LOOKBACK_DAYS, 2)]


def _timed_nearby(user_id: str, at: datetime) -> list[ColumnElement]:
    days = nearby_days(at)
    return [
        Schedule.user_id == user_id,
        Schedule.date >= days[0],
        Schedule.date <= days[-1],
        Schedule.starts_at.is_not(None),
        Schedule.ends_at.is_not(None),
    ]


def open_for_clock_in(db: Session, user_id: str, at: datetime) -> list[Schedule]:
    """Assignments whose window, from the early allowance before the start until the end, holds the instant and that no clock-in has used."""
    return list(
        db.scalars(
            select(Schedule).where(
                *_timed_nearby(user_id, at),
                Schedule.starts_at <= at + timedelta(minutes=CLOCK_IN_EARLY_MINUTES),
                Schedule.ends_at >= at,
                Schedule.clock_in_used.is_(False),
            )
        ).all()
    )


def around(db: Session, user_id: str, at: datetime) -> list[Schedule]:
    """The same nearby assignments, used or not, to tell why a clock-in is not open."""
    return list(db.scalars(select(Schedule).where(*_timed_nearby(user_id, at))).all())


def claim_for_clock_in(db: Session, schedule_id: str) -> bool:
    """Marks the assignment used in one conditional statement, so of two requests at the same moment only one wins."""
    result = db.execute(
        update(Schedule)
        .where(Schedule.id == schedule_id, Schedule.clock_in_used.is_(False))
        .values(clock_in_used=True)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1


def offered_for_clock_in(db: Session, user_id: str, at: datetime) -> Schedule | None:
    """The assignment shown on the clock-in screen; when two windows overlap, the one starting nearest to the instant."""
    return min(
        open_for_clock_in(db, user_id, at),
        key=lambda schedule: abs(as_aware(schedule.starts_at) - at),
        default=None,
    )
