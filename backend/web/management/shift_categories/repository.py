"""Database reads for the shift categories."""
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.shift_code import ShiftCode


def categories(db: Session, kind: str) -> list[Category]:
    return list(db.scalars(select(Category).where(Category.kind == kind).order_by(func.lower(Category.name), Category.id)).all())


def find(db: Session, kind: str, category_id: str) -> Category | None:
    return db.scalar(select(Category).where(Category.kind == kind, Category.id == category_id))


def find_for_update(db: Session, kind: str, category_id: str) -> Category | None:
    """Baris kategori dikunci, sehingga kode yang dibuat bersamaan menunggu dan tidak sempat memakai kategori yang sedang dihapus."""
    return db.scalar(select(Category).where(Category.kind == kind, Category.id == category_id).with_for_update())


def code_count(db: Session, category_id: str) -> int:
    return db.scalar(select(func.count()).select_from(ShiftCode).where(ShiftCode.category_id == category_id)) or 0


def name_owner(db: Session, kind: str, name: str) -> Category | None:
    return db.scalar(select(Category).where(Category.kind == kind, func.lower(Category.name) == name.lower()))


def codes_by_category(db: Session, category_ids: list[str] | None = None) -> dict[str, list[ShiftCode]]:
    """Every code grouped by its category in one query; the table holds a few hundred rows at most."""
    statement = select(ShiftCode).where(ShiftCode.category_id.is_not(None))
    if category_ids is not None:
        statement = statement.where(ShiftCode.category_id.in_(category_ids))
    grouped: dict[str, list[ShiftCode]] = defaultdict(list)
    for code in db.scalars(statement).all():
        grouped[code.category_id].append(code)
    return grouped
