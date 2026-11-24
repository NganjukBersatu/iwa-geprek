"""Database reads for the shift code groups."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.outlet import Outlet
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


def rows(db: Session, outlet_id: str | None) -> list[ShiftCode]:
    statement = select(ShiftCode).outerjoin(Category, Category.id == ShiftCode.category_id)
    if outlet_id:
        statement = statement.where(ShiftCode.outlet_id == outlet_id)
    return list(db.scalars(statement.order_by(ShiftCode.sort_order, Category.name, ShiftCode.code)).all())


def rows_of_group(db: Session, key: str, outlet_id: str | None) -> list[ShiftCode]:
    """A row without a master id is a group of its own, named by its id."""
    statement = select(ShiftCode).where(or_(ShiftCode.master_id == key, (ShiftCode.master_id.is_(None)) & (ShiftCode.id == key)))
    if outlet_id:
        statement = statement.where(ShiftCode.outlet_id == outlet_id)
    return list(db.scalars(statement.order_by(ShiftCode.outlet_id)).all())


def outlets(db: Session) -> list[Outlet]:
    return list(db.scalars(select(Outlet).order_by(Outlet.name)).all())


def assignments_by_code(db: Session) -> dict[str, int]:
    return {code_id: count for code_id, count in db.execute(select(Schedule.shift_code_id, func.count()).where(Schedule.shift_code_id.is_not(None)).group_by(Schedule.shift_code_id)).all()}


def category_named(db: Session, kind: str, name: str) -> Category | None:
    return db.scalar(select(Category).where(Category.kind == kind, func.lower(Category.name) == name.lower()))


def category_names(db: Session, kind: str) -> list[str]:
    return list(db.scalars(select(Category.name).where(Category.kind == kind).order_by(Category.name)).all())
