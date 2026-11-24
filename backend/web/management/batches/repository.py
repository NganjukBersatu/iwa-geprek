"""Database reads for the admin's batches."""
from sqlalchemy import ColumnElement, exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.outlet import Outlet
from app.core import protection
from app.core.search import contains
from app.core.sorting import SqlSorting
from app.models.outlet_batch import OutletBatch, OutletBatchItem, OutletBatchShiftCode
from app.models.shift_code import ShiftCode
from app.models.user import User
from web.management.batches.domain import BatchQuery


def find_outlet(db: Session, outlet_id: str) -> Outlet | None:
    return db.get(Outlet, outlet_id)


def find_batch(db: Session, batch_id: str) -> OutletBatch | None:
    return db.get(OutletBatch, batch_id)


# Cabang demi cabang, lalu urutan dan jam mulainya; "days" mengurutkan dari satuan pola berulangnya.
SORTING = SqlSorting(
    columns={
        "name": OutletBatch.name,
        "outlet": Outlet.name,
        "hours": OutletBatch.start_clock,
        "days": OutletBatch.repeat_unit,
        "items": select(func.count()).where(OutletBatchItem.batch_id == OutletBatch.id).scalar_subquery(),
        "status": OutletBatch.is_active,
    },
    default=(Outlet.name, OutletBatch.sort_order, OutletBatch.start_clock),
    tiebreak=OutletBatch.id,
)


def _conditions(query: BatchQuery) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if query.outlet_id is not None:
        conditions.append(OutletBatch.outlet_id == query.outlet_id)
    if query.kind is not None:
        conditions.append(OutletBatch.kind == query.kind)
    if query.active is not None:
        conditions.append(OutletBatch.is_active.is_(query.active))
    if query.fill_mode is not None:
        conditions.append(OutletBatch.fill_mode == query.fill_mode)
    if query.repeat_unit is not None:
        conditions.append(OutletBatch.repeat_unit == query.repeat_unit)
    if query.shift_code_id is not None:
        conditions.append(
            exists().where(OutletBatchShiftCode.batch_id == OutletBatch.id, OutletBatchShiftCode.shift_code_id == query.shift_code_id)
        )
    if query.search:
        labelled = exists().where(OutletBatchItem.batch_id == OutletBatch.id, contains(OutletBatchItem.label, query.search))
        conditions.append(or_(contains(OutletBatch.name, query.search), labelled))
    return conditions


def batch_page(db: Session, query: BatchQuery, sort: str | None, page: int, size: int) -> tuple[list[OutletBatch], int]:
    """Satu halaman templat beserta jumlah seluruhnya yang cocok; cari, saring, dan urut dikerjakan database."""
    conditions = _conditions(query)
    total = db.scalar(select(func.count()).select_from(OutletBatch).where(*conditions)) or 0
    rows = db.scalars(
        select(OutletBatch)
        .join(Outlet, Outlet.id == OutletBatch.outlet_id)
        .where(*conditions)
        .order_by(*SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(rows), total


def branch_user(db: Session, outlet_id: str, search: str | None, page: int, size: int) -> tuple[list[User], int]:
    """Karyawan aktif satu cabang yang bisa diberi tugas, dicari dan dihalamankan di server supaya daftarnya tidak terpotong."""
    conditions = [User.outlet_id == outlet_id, User.is_active.is_(True), protection.schedulable()]
    if search:
        conditions.append(or_(contains(User.name, search), contains(User.username, search)))
    total = db.scalar(select(func.count()).select_from(User).where(*conditions)) or 0
    rows = db.scalars(select(User).where(*conditions).order_by(User.name, User.username, User.id).offset((page - 1) * size).limit(size)).all()
    return list(rows), total


def branch_user_by_ids(db: Session, outlet_id: str, user_ids: set[str]) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(User.id.in_(user_ids), User.outlet_id == outlet_id, User.is_active.is_(True), protection.schedulable())
            .order_by(User.name, User.username, User.id)
        ).all()
    )


def named_like(db: Session, outlet_id: str, kind: str, name: str) -> bool:
    """Apakah cabang itu sudah punya templat berjenis sama dengan nama yang sama, tanpa membedakan huruf besar kecil."""
    return db.scalar(
        select(exists().where(OutletBatch.outlet_id == outlet_id, OutletBatch.kind == kind, func.lower(OutletBatch.name) == name.lower()))
    ) or False


def lock_for_copy(db: Session, batch_id: str) -> None:
    """Menyerialkan penyalinan satu tugas, supaya klik ganda tidak membuat salinan ganda."""
    db.execute(select(func.pg_advisory_xact_lock(func.hashtext(batch_id))))


def working_shift_codes(db: Session, outlet_id: str) -> list[ShiftCode]:
    """Kode shift kerja satu cabang; kode libur tidak bisa diberi tugas."""
    return list(
        db.scalars(
            select(ShiftCode)
            .where(ShiftCode.outlet_id == outlet_id, ShiftCode.is_day_off.is_(False))
            .order_by(ShiftCode.sort_order, ShiftCode.code, ShiftCode.id)
        ).all()
    )
