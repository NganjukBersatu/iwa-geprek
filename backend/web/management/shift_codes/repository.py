"""Database reads and set-based writes for shift codes."""
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.day_off import DayOff
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


def codes(db: Session, outlet_id: str | None) -> list[ShiftCode]:
    statement = select(ShiftCode).outerjoin(Category, Category.id == ShiftCode.category_id)
    if outlet_id:
        statement = statement.where(ShiftCode.outlet_id == outlet_id)
    return list(db.scalars(statement.order_by(ShiftCode.sort_order, Category.name, ShiftCode.code)).all())


def find(db: Session, code_id: str) -> ShiftCode | None:
    return db.get(ShiftCode, code_id)


def code_owner(db: Session, outlet_id: str, code: str) -> ShiftCode | None:
    return db.scalar(select(ShiftCode).where(ShiftCode.outlet_id == outlet_id, func.lower(ShiftCode.code) == code.lower()))


def any_named(db: Session, code: str) -> bool:
    return db.scalar(select(ShiftCode.id).where(func.lower(ShiftCode.code) == code.lower()).limit(1)) is not None


def category_exists(db: Session, kind: str, category_id: str) -> bool:
    return db.scalar(select(Category.id).where(Category.id == category_id, Category.kind == kind)) is not None


def category_by_id(db: Session, category_id: str) -> Category | None:
    return db.get(Category, category_id)


def upcoming_schedules(db: Session, code_id: str, first_day: date) -> list[Schedule]:
    return list(db.scalars(select(Schedule).where(Schedule.shift_code_id == code_id, Schedule.date >= first_day)).all())


def detach_from_schedules(db: Session, code_id: str) -> None:
    db.execute(update(Schedule).where(Schedule.shift_code_id == code_id).values(shift_code_id=None))


def detach_from_days_off(db: Session, code_id: str) -> None:
    db.execute(update(DayOff).where(DayOff.shift_code_id == code_id).values(shift_code_id=None))
