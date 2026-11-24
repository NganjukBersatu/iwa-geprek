"""The one door for the visitor kinds and genders a cashier picks on an order; both lists belong to each branch and the admin writes them."""
import uuid
from dataclasses import dataclass

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core import master_id
from app.core.errors import DomainError
from app.models.order import Order
from app.models.visitor import VisitorCategory, VisitorGender

SECTION_CATEGORY = "kategori"
SECTION_GENDER = "gender"
PERMISSION_MANAGE = "pengunjung.kelola"
NOT_FOUND = 404
CONFLICT = 409

CATEGORY_NOT_FOUND = "Kategori pengunjung tidak ditemukan."
GENDER_NOT_FOUND = "Pilihan gender tidak ditemukan."
NAME_REQUIRED = "Nama wajib diisi."
NAME_TAKEN = "'{name}' sudah ada di cabang ini."
IN_USE = "Pilihan ini sudah dipakai pesanan, jadi tidak bisa dihapus. Nonaktifkan agar tidak muncul di kasir dan riwayat tetap utuh."

# Where a new branch starts; the admin renames, adds or switches them off afterwards.
DEFAULT_CATEGORIES = (("Sendiri", True), ("Berkeluarga", False), ("Datang bersama teman", False), ("Pasangan", False))
DEFAULT_GENDERS = ("Laki-laki", "Perempuan")


@dataclass(frozen=True)
class Picked:
    """What an order keeps; a copy of the names, so renaming or deleting later leaves old orders readable."""

    category: VisitorCategory | None
    gender: VisitorGender | None


def _tidy(name: str) -> str:
    tidy = master_id.tidy(name)
    if not tidy:
        raise DomainError(NAME_REQUIRED)
    return tidy


def categories_of(db: Session, outlet_id: str) -> list[VisitorCategory]:
    return list(db.scalars(select(VisitorCategory).where(VisitorCategory.outlet_id == outlet_id).order_by(VisitorCategory.position, VisitorCategory.name)).all())


def genders_of(db: Session, outlet_id: str) -> list[VisitorGender]:
    return list(db.scalars(select(VisitorGender).where(VisitorGender.outlet_id == outlet_id).order_by(VisitorGender.position, VisitorGender.name)).all())


def usage(db: Session, column, outlet_id: str) -> dict[str, int]:
    """How many orders of the branch carry each choice, in one grouped query, so the screen can say so before a delete."""
    rows = db.execute(select(column, func.count(Order.id)).where(Order.outlet_id == outlet_id, column.is_not(None)).group_by(column)).all()
    return {choice_id: count for choice_id, count in rows}


def _check_name(db: Session, model, outlet_id: str, name: str, except_id: str | None) -> None:
    found = db.scalar(select(model.id).where(model.outlet_id == outlet_id, func.lower(model.name) == name.lower()))
    if found is not None and found != except_id:
        raise DomainError(NAME_TAKEN.format(name=name), status=CONFLICT)


def _next_position(db: Session, model, outlet_id: str) -> int:
    return (db.scalar(select(func.max(model.position)).where(model.outlet_id == outlet_id)) or 0) + 1


def create_category(db: Session, outlet_id: str, name: str, asks_gender: bool, active: bool) -> VisitorCategory:
    name = _tidy(name)
    _check_name(db, VisitorCategory, outlet_id, name, None)
    row = VisitorCategory(
        id=str(uuid.uuid4()),
        outlet_id=outlet_id,
        master_id=master_id.for_new_row(db, VisitorCategory, VisitorCategory.name, name, outlet_id),
        name=name,
        asks_gender=asks_gender,
        position=_next_position(db, VisitorCategory, outlet_id),
        is_active=active,
    )
    db.add(row)
    db.commit()
    return row


def update_category(db: Session, outlet_id: str, category_id: str, name: str, asks_gender: bool, active: bool) -> VisitorCategory:
    row = db.get(VisitorCategory, category_id)
    if row is None or row.outlet_id != outlet_id:
        raise DomainError(CATEGORY_NOT_FOUND, status=NOT_FOUND)
    name = _tidy(name)
    _check_name(db, VisitorCategory, outlet_id, name, row.id)
    row.name, row.asks_gender, row.is_active = name, asks_gender, active
    db.commit()
    return row


def delete_category(db: Session, outlet_id: str, category_id: str) -> None:
    """A kind no order has used is deleted for real; a used one is only switched off, so every order keeps its link."""
    row = db.get(VisitorCategory, category_id)
    if row is None or row.outlet_id != outlet_id:
        raise DomainError(CATEGORY_NOT_FOUND, status=NOT_FOUND)
    if db.scalar(select(exists().where(Order.visitor_category_id == row.id))):
        raise DomainError(IN_USE, status=CONFLICT)
    db.delete(row)
    db.commit()


def create_gender(db: Session, outlet_id: str, name: str, active: bool) -> VisitorGender:
    name = _tidy(name)
    _check_name(db, VisitorGender, outlet_id, name, None)
    row = VisitorGender(id=str(uuid.uuid4()), outlet_id=outlet_id, name=name, position=_next_position(db, VisitorGender, outlet_id), is_active=active)
    db.add(row)
    db.commit()
    return row


def update_gender(db: Session, outlet_id: str, gender_id: str, name: str, active: bool) -> VisitorGender:
    row = db.get(VisitorGender, gender_id)
    if row is None or row.outlet_id != outlet_id:
        raise DomainError(GENDER_NOT_FOUND, status=NOT_FOUND)
    name = _tidy(name)
    _check_name(db, VisitorGender, outlet_id, name, row.id)
    row.name, row.is_active = name, active
    db.commit()
    return row


def delete_gender(db: Session, outlet_id: str, gender_id: str) -> None:
    row = db.get(VisitorGender, gender_id)
    if row is None or row.outlet_id != outlet_id:
        raise DomainError(GENDER_NOT_FOUND, status=NOT_FOUND)
    if db.scalar(select(exists().where(Order.visitor_gender_id == row.id))):
        raise DomainError(IN_USE, status=CONFLICT)
    db.delete(row)
    db.commit()


def picked(db: Session, outlet_id: str, category_id: str | None, gender_id: str | None) -> Picked:
    """A stale pick (deleted, switched off, another branch) is dropped, never a reason to refuse a sale; gender counts only where the kind asks for it."""
    category = db.get(VisitorCategory, category_id) if category_id else None
    if category is None or category.outlet_id != outlet_id or not category.is_active:
        return Picked(None, None)
    gender = db.get(VisitorGender, gender_id) if gender_id and category.asks_gender else None
    if gender is not None and (gender.outlet_id != outlet_id or not gender.is_active):
        gender = None
    return Picked(category, gender)


def seed_defaults(db: Session, outlet_id: str) -> None:
    """The lists a new branch starts with; the caller commits."""
    for position, (name, asks_gender) in enumerate(DEFAULT_CATEGORIES):
        db.add(
            VisitorCategory(
                id=str(uuid.uuid4()),
                outlet_id=outlet_id,
                master_id=master_id.for_new_row(db, VisitorCategory, VisitorCategory.name, name, outlet_id),
                name=name,
                asks_gender=asks_gender,
                position=position,
                is_active=True,
            )
        )
    for position, name in enumerate(DEFAULT_GENDERS):
        db.add(VisitorGender(id=str(uuid.uuid4()), outlet_id=outlet_id, name=name, position=position, is_active=True))
    db.flush()
