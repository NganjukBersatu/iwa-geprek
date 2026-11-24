"""Database reads for the day plan."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.employee.schedule.constants import LOOKBACK_DAYS
from app.models.overtime import Overtime
from app.models.schedule import Schedule


def schedules_around(db: Session, user_id: str, day: date) -> list[Schedule]:
    return list(
        db.scalars(
            select(Schedule).where(
                Schedule.user_id == user_id,
                Schedule.date >= day - timedelta(days=LOOKBACK_DAYS),
                Schedule.date <= day,
            )
        ).all()
    )


def unplanned_around(db: Session, user_id: str, day: date) -> list[Overtime]:
    return list(
        db.scalars(
            select(Overtime).where(
                Overtime.user_id == user_id,
                Overtime.end_at.is_not(None),
                Overtime.date >= day - timedelta(days=LOOKBACK_DAYS),
            )
        ).all()
    )
