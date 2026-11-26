"""Branches: what differs physically between cafes, such as where attendance counts as on site.

Menutup cabang menonaktifkannya supaya laporannya tetap terbaca; hapus permanen hanya untuk cabang yang sudah tutup dan menghapus seluruh datanya.
"""
import uuid
from datetime import date

from sqlalchemy import select, update as sql_update
from sqlalchemy.orm import Session

from app.core import branch_periods, branch_settings, live, visitors
from app.core.auth import end_sessions_of
from app.core.clock import now
from app.core.clock import today
from app.core.errors import DomainError
from app.core.finance.payment_methods import seed_defaults
from app.models.outlet import Outlet
from app.models.user import User
from web.management.branches import messages, removal, repository
from web.management.branches.constants import CONFLICT, DEFAULT_RADIUS_METERS, NOT_FOUND
from web.management.branches.domain import BranchChanges, BranchDraft

ATTRIBUTES = {
    "name": "name",
    "code": "code",
    "receipt_number": "receipt_number",
    "is_active": "is_active",
    "google_review_url": "google_review_url",
    "google_location_id": "google_location_id",
    "latitude": "latitude",
    "longitude": "longitude",
    "attendance_radius_meters": "attendance_radius_meters",
    "cash_float": "cash_float",
    "spending_float": "spending_float",
}


def list_branches(db: Session, admin: User) -> list[Outlet]:
    return repository.branches(db, admin.locked_outlet_id)


def get(db: Session, admin: User, outlet_id: str) -> Outlet:
    outlet = repository.find(db, outlet_id)
    locked = admin.locked_outlet_id
    if outlet is None or (locked and outlet.id != locked):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return outlet


def create(db: Session, draft: BranchDraft) -> Outlet:
    name = _tidy(draft.name)
    if not name:
        raise DomainError(messages.NAME_REQUIRED, field="name")
    outlet = Outlet(
        id=str(uuid.uuid4()),
        name=name,
        code=_blank(draft.code),
        receipt_number=_blank(draft.receipt_number),
        is_active=True,
        google_review_url=_blank(draft.google_review_url),
        google_location_id=_blank(draft.google_location_id),
        latitude=draft.latitude,
        longitude=draft.longitude,
        attendance_radius_meters=draft.attendance_radius_meters or DEFAULT_RADIUS_METERS,
        cash_float=draft.cash_float,
        spending_float=draft.spending_float,
    )
    db.add(outlet)
    db.flush()
    seed_defaults(db, outlet.id)
    visitors.seed_defaults(db, outlet.id)
    branch_settings.ensure(db, outlet.id)
    _set_period(db, outlet.id, draft.period_start, draft.period_end)
    db.commit()
    db.refresh(outlet)
    return outlet


def update(db: Session, admin: User, outlet_id: str, changes: BranchChanges) -> Outlet:
    outlet = get(db, admin, outlet_id)
    values = dict(changes.values)
    _set_period(db, outlet.id, values.pop("period_start", None), values.pop("period_end", None))
    for field, value in values.items():
        if field == "attendance_radius_meters" and value is None:
            raise DomainError(messages.RADIUS_REQUIRED, field="attendance_radius_meters")
        if field == "is_active" and value is None:
            continue
        if field == "is_active" and value and outlet.removal_started_at is not None:
            raise DomainError(messages.REMOVAL_STARTED, status=CONFLICT)
        if isinstance(value, str):
            value = _tidy(value) if field == "name" else _blank(value)
            if field == "name" and not value:
                raise DomainError(messages.NAME_REQUIRED, field="name")
        setattr(outlet, ATTRIBUTES[field], value)
    db.commit()
    db.refresh(outlet)
    return outlet


def remove(db: Session, admin: User, outlet_id: str, typed_name: str) -> removal.Progress:
    """Satu langkah hapus permanen; layar memanggil lagi sampai selesai, dan panggilan ulang melanjutkan dari sisa terakhir."""
    outlet = get(db, admin, outlet_id)
    if outlet.is_active:
        raise DomainError(messages.REMOVAL_ACTIVE, status=CONFLICT)
    if _tidy(typed_name) != _tidy(outlet.name):
        raise DomainError(messages.REMOVAL_NAME_MISMATCH)
    if admin.outlet_id == outlet.id:
        raise DomainError(messages.REMOVAL_OWN_BRANCH, status=CONFLICT)
    if outlet.removal_started_at is None:
        outlet.removal_started_at = now()
        _release_user(db, outlet.id)
        db.commit()
    parts = removal.plan(db)
    progress = removal.step(db, outlet.id, parts)
    if not progress.done:
        return progress
    live.mark(db, removal.changed_tables(db, parts))
    db.delete(db.get(Outlet, outlet.id))
    db.commit()
    return progress


def _release_user(db: Session, outlet_id: str) -> None:
    """Akun karyawan cabang ini tetap ada beserta riwayatnya, tetapi dilepas dan dinonaktifkan; akun tanpa cabang yang aktif bisa membuka semua cabang."""
    user_ids = list(db.scalars(select(User.id).where(User.outlet_id == outlet_id)))
    if not user_ids:
        return
    db.execute(sql_update(User).where(User.id.in_(user_ids)).values(outlet_id=None, is_active=False))
    end_sessions_of(db, user_ids)


def adjust_period(db: Session, admin: User, outlet_id: str, original_start: date, start: date, end: date) -> None:
    get(db, admin, outlet_id)
    branch_periods.adjust(db, outlet_id, original_start, start, end, today())
    db.commit()


def reset_period(db: Session, admin: User, outlet_id: str, start: date) -> None:
    get(db, admin, outlet_id)
    branch_periods.reset(db, outlet_id, start)
    db.commit()


def _set_period(db: Session, outlet_id: str, start: date | None, end: date | None) -> None:
    """Periode berjalan dari dialog cabang menjadi pola bulan-bulan sesudahnya, di transaksi yang sama dengan cabangnya."""
    if start is None and end is None:
        return
    if start is None or end is None:
        raise DomainError(messages.PERIOD_INCOMPLETE)
    branch_periods.set_pattern(db, outlet_id, start, end)


def _tidy(text: str) -> str:
    return " ".join(text.split())


def _blank(text: str | None) -> str | None:
    """Text pasted from a dashboard often carries spaces or a newline at its end; empty becomes none."""
    return (text or "").strip() or None
