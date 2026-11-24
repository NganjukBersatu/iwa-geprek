"""Database reads for days off."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.day_off import DayOff
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


def in_range(db: Session, start: date, end: date, outlet_id: str | None) -> list[DayOff]:
    filters = [DayOff.date >= start, DayOff.date <= end]
    if outlet_id:
        filters.append(DayOff.outlet_id == outlet_id)
    return list(db.scalars(select(DayOff).where(*filters).order_by(DayOff.date)).all())


def find(db: Session, day_off_id: str) -> DayOff | None:
    return db.get(DayOff, day_off_id)


def find_code(db: Session, code_id: str) -> ShiftCode | None:
    return db.get(ShiftCode, code_id)


def scheduled_on(db: Session, day: date, user_id: str) -> bool:
    return db.scalar(select(Schedule.id).where(Schedule.date == day, Schedule.user_id == user_id)) is not None


def off_on(db: Session, day: date, user_id: str) -> bool:
    return db.scalar(select(DayOff.id).where(DayOff.date == day, DayOff.user_id == user_id)) is not None
