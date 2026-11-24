"""The choices for a note on a whole order ("Ulang tahun", ...): each branch has its own, which its cashier extends from the till and its manager keeps tidy on the tablet."""
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import master_id
from app.core.search import contains
from app.core.errors import DomainError
from app.models.category import Category
from app.models.order import Order

KIND = "catatan_order"
# Adding a choice only needs the right to sell; renaming and deleting stay with the reference lists on the web.
PERMISSION_ADD = "order.buat"
PERMISSION_MANAGE = "referensi.kelola"
MAX_NAME_LENGTH = 100
NOT_FOUND_STATUS = 404
CONFLICT_STATUS = 409
FORBIDDEN_STATUS = 403

NAME_REQUIRED = "Catatan wajib diisi."
NAME_TAKEN = "Catatan dengan nama itu sudah ada."
NOT_FOUND = "Catatan tidak ditemukan."
SHARED_WEB_ONLY = "Catatan umum berlaku di semua cabang dan hanya bisa diatur dari web admin."
IN_USE = "Catatan ini sudah dipakai {count} pesanan, jadi tidak bisa dihapus. Ganti namanya bila salah ketik."


def listed(db: Session, outlet_id: str | None = None) -> list[Category]:
    """Catatan satu cabang beserta catatan umum lama; tanpa cabang, semua catatan semua cabang (untuk web)."""
    statement = select(Category).where(Category.kind == KIND)
    if outlet_id is not None:
        statement = statement.where(or_(Category.outlet_id == outlet_id, Category.outlet_id.is_(None)))
    return list(db.scalars(statement.order_by(func.lower(Category.name), Category.id)))


def page_of(db: Session, outlet_id: str, search: str | None, sort: str | None, page: int, size: int, created_by_id: str | None = None) -> tuple[list[Category], int]:
    """Satu halaman catatan yang terlihat di cabang itu, urut nama naik atau turun; [created_by_id] hanya menyisakan catatan buatan orang itu."""
    filters = [Category.kind == KIND, or_(Category.outlet_id == outlet_id, Category.outlet_id.is_(None))]
    if search:
        filters.append(contains(Category.name, search))
    if created_by_id:
        filters.append(Category.created_by_id == created_by_id)
    total = db.scalar(select(func.count()).select_from(Category).where(*filters)) or 0
    order = func.lower(Category.name).desc() if sort == "-name" else func.lower(Category.name).asc()
    rows = db.scalars(select(Category).where(*filters).order_by(order, Category.id).offset((page - 1) * size).limit(size))
    return list(rows), total


def _named(db: Session, name: str, outlet_id: str | None) -> Category | None:
    """Catatan bernama itu di cabang tersebut; catatan umum lama dengan nama yang sama ikut dihitung sebagai yang sudah ada."""
    rows = list(db.scalars(select(Category).where(Category.kind == KIND, func.lower(Category.name) == name.lower(), or_(Category.outlet_id == outlet_id, Category.outlet_id.is_(None)))))
    own = [row for row in rows if row.outlet_id == outlet_id]
    return (own or rows or [None])[0]


def _twin(db: Session, name: str, outlet_id: str | None) -> Category | None:
    """Catatan lain dengan nama yang sama di lingkup yang sama persis, yang tidak boleh ada dua."""
    return db.scalar(select(Category).where(Category.kind == KIND, func.lower(Category.name) == name.lower(), Category.outlet_id.is_(None) if outlet_id is None else Category.outlet_id == outlet_id))


def ensure(db: Session, name: str, outlet_id: str, user_id: str) -> Category:
    """Catatan dengan nama ini di cabang itu, dibuat atas nama [user_id] bila belum ada; commit."""
    tidy = master_id.tidy(name)
    if not tidy:
        raise DomainError(NAME_REQUIRED)
    found = _named(db, tidy, outlet_id)
    if found is not None:
        return found
    row = Category(id=str(uuid.uuid4()), kind=KIND, name=tidy, outlet_id=outlet_id, created_by_id=user_id)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        # Dua tablet menambah nama yang sama bersamaan: yang kedua mendapat baris yang pertama.
        db.rollback()
        found = _named(db, tidy, outlet_id)
        if found is None:
            raise
        return found
    return row


def usage(db: Session, note_ids: list[str]) -> dict[str, int]:
    """How many orders carry each note, read through ix_orders_catatan."""
    if not note_ids:
        return {}
    rows = db.execute(select(Order.note_id, func.count()).where(Order.note_id.in_(note_ids)).group_by(Order.note_id))
    return {note_id: count for note_id, count in rows}


def _row(db: Session, note_id: str, outlet_scope: str | None) -> Category:
    """Dengan [outlet_scope] (tablet) hanya catatan cabang itu yang bisa diatur; catatan umum lama hanya dari web, dan catatan cabang lain tampak tidak ada."""
    row = db.scalar(select(Category).where(Category.id == note_id, Category.kind == KIND))
    if row is None or (outlet_scope is not None and row.outlet_id not in (None, outlet_scope)):
        raise DomainError(NOT_FOUND, status=NOT_FOUND_STATUS)
    if outlet_scope is not None and row.outlet_id is None:
        raise DomainError(SHARED_WEB_ONLY, status=FORBIDDEN_STATUS)
    return row


def get(db: Session, note_id: str) -> Category:
    """One note for its page; an unknown ID answers as missing."""
    return _row(db, note_id, None)


def rename(db: Session, note_id: str, name: str, outlet_scope: str | None = None) -> Category:
    """Memperbaiki salah ketik tanpa menyentuh pesanan lama, yang tetap memegang label saat dijual; commit."""
    row = _row(db, note_id, outlet_scope)
    tidy = master_id.tidy(name)
    if not tidy:
        raise DomainError(NAME_REQUIRED)
    twin = _twin(db, tidy, row.outlet_id)
    if twin is not None and twin.id != row.id:
        raise DomainError(NAME_TAKEN, status=CONFLICT_STATUS)
    row.name = tidy
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DomainError(NAME_TAKEN, status=CONFLICT_STATUS) from error
    return row


def remove(db: Session, note_id: str, outlet_scope: str | None = None) -> None:
    """Hanya catatan yang tidak dibawa pesanan mana pun yang bisa dihapus; yang terpakai diganti nama, supaya tak ada pesanan yang kehilangan tautannya; commit."""
    row = _row(db, note_id, outlet_scope)
    used = usage(db, [note_id]).get(note_id, 0)
    if used > 0:
        raise DomainError(IN_USE.format(count=used), status=CONFLICT_STATUS)
    db.delete(row)
    db.commit()


def picked(db: Session, note_id: str | None, outlet_id: str | None = None) -> Category | None:
    """Pilihan yang sudah dihapus saat kasir mengisi pesanan dilepas, tidak pernah menjadi alasan menolak penjualan; catatan cabang lain juga dilepas."""
    if not note_id:
        return None
    row = db.scalar(select(Category).where(Category.id == note_id, Category.kind == KIND))
    if row is not None and outlet_id is not None and row.outlet_id not in (None, outlet_id):
        return None
    return row
