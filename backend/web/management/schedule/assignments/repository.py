"""Database reads for assignments."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.sorting import SqlSorting
from app.models.role import Role
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode
from app.models.user import User


_USER = select(User.username).where(User.id == Schedule.user_id).scalar_subquery()

SORTING = SqlSorting(
    columns={
        "user": _USER,
        "date": Schedule.date,
        "code": select(ShiftCode.code).where(ShiftCode.id == Schedule.shift_code_id).scalar_subquery(),
        "role": select(Role.name).where(Role.id == Schedule.role_id).scalar_subquery(),
        "note": Schedule.note,
    },
    default=(Schedule.date, func.lower(_USER)),
    tiebreak=Schedule.id,
)


def in_range(db: Session, start: date, end: date, outlet_id: str | None, user_id: str | None, sort: str | None) -> list[Schedule]:
    filters = [Schedule.date >= start, Schedule.date <= end]
    if outlet_id:
        filters.append(Schedule.outlet_id == outlet_id)
    if user_id:
        filters.append(Schedule.user_id == user_id)
    return list(db.scalars(select(Schedule).where(*filters).order_by(*SORTING.order_by(sort))).all())


def find(db: Session, schedule_id: str) -> Schedule | None:
    return db.get(Schedule, schedule_id)


def find_code(db: Session, code_id: str) -> ShiftCode | None:
    return db.get(ShiftCode, code_id)


def role_exists(db: Session, role_id: str) -> bool:
    return db.get(Role, role_id) is not None


def same_slot(db: Session, day: date, shift_code_id: str | None, user_id: str) -> Schedule | None:
    return db.scalar(
        select(Schedule).where(Schedule.date == day, Schedule.shift_code_id == shift_code_id, Schedule.user_id == user_id)
    )
