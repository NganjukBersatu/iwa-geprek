"""Database reads for the schedule screens."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.day_off import DayOff
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


def assignments_between(db: Session, first: date, last: date, outlet_id: str | None) -> list[Schedule]:
    query = select(Schedule).where(Schedule.date >= first, Schedule.date <= last)
    if outlet_id:
        query = query.where(Schedule.outlet_id == outlet_id)
    return list(db.scalars(query.order_by(Schedule.date, Schedule.starts_at)).all())


def assignments_of(db: Session, user_id: str, day: date) -> list[Schedule]:
    return list(
        db.scalars(
            select(Schedule).where(Schedule.user_id == user_id, Schedule.date == day).order_by(Schedule.starts_at)
        ).all()
    )


def days_off_between(db: Session, first: date, last: date, outlet_id: str | None) -> list[DayOff]:
    query = select(DayOff).where(DayOff.date >= first, DayOff.date <= last)
    if outlet_id:
        query = query.where(DayOff.outlet_id == outlet_id)
    return list(db.scalars(query.order_by(DayOff.date)).all())


def shift_codes(db: Session, outlet_id: str | None) -> list[ShiftCode]:
    query = select(ShiftCode).outerjoin(Category, Category.id == ShiftCode.category_id)
    if outlet_id:
        query = query.where(ShiftCode.outlet_id == outlet_id)
    return list(db.scalars(query.order_by(ShiftCode.sort_order, Category.name, ShiftCode.code)).all())
