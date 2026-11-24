"""Pengajuan tutup periode stok opname: diajukan dari tablet cabang, diputus admin di web; satu pintu untuk keduanya."""
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.ingredients import openings
from app.core.clock import now
from app.core.errors import DomainError
from app.models.ingredient import REQUEST_CLOSED, REQUEST_PENDING, REQUEST_REJECTED, IngredientCountRequest
from app.models.user import User

NOT_FOUND = 404
CONFLICT = 409
ALREADY_PENDING = "Pengajuan tutup periode cabang ini masih menunggu admin."
REQUEST_NOT_FOUND = "Pengajuan tidak ditemukan"
ALREADY_DECIDED = "Pengajuan ini sudah diputus."


def submit(db: Session, user: User, outlet_id: str, note: str | None) -> IngredientCountRequest:
    """Satu pintu pengajuan dari tablet dan web; indeks unik parsial di database menjadi wasit bila dua pengajuan datang bersamaan."""
    period_start = openings.running_start(db, outlet_id)
    if db.scalar(select(IngredientCountRequest.id).where(IngredientCountRequest.outlet_id == outlet_id, IngredientCountRequest.status == REQUEST_PENDING)):
        raise DomainError(ALREADY_PENDING, status=CONFLICT)
    request = IngredientCountRequest(outlet_id=outlet_id, period_start=period_start, note=(note or "").strip() or None, requested_by=user.id)
    db.add(request)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DomainError(ALREADY_PENDING, status=CONFLICT) from error
    return request


def current(db: Session, outlet_id: str) -> IngredientCountRequest | None:
    """Pengajuan terakhir cabang ini apa pun periodenya, supaya pengaju tetap melihat langkah Periode ditutup setelah periode baru mulai."""
    return db.scalars(
        select(IngredientCountRequest)
        .where(IngredientCountRequest.outlet_id == outlet_id)
        .order_by(IngredientCountRequest.created_at.desc(), IngredientCountRequest.id.desc())
        .limit(1)
    ).first()


def latest(db: Session, outlet_id: str, period_start: date) -> IngredientCountRequest | None:
    """Pengajuan terakhir untuk periode berjalan cabang ini, apa pun keputusannya."""
    return db.scalars(
        select(IngredientCountRequest)
        .where(IngredientCountRequest.outlet_id == outlet_id, IngredientCountRequest.period_start == period_start)
        .order_by(IngredientCountRequest.created_at.desc(), IngredientCountRequest.id.desc())
        .limit(1)
    ).first()


def shown(db: Session, outlet_id: str, period_start: date) -> IngredientCountRequest | None:
    """Yang ditampilkan di tablet: pengajuan yang masih menunggu apa pun periodenya, jadi tidak hilang bila awal periode bergeser; selain itu pengajuan terakhir periode berjalan."""
    waiting = db.scalars(
        select(IngredientCountRequest)
        .where(IngredientCountRequest.outlet_id == outlet_id, IngredientCountRequest.status == REQUEST_PENDING)
        .order_by(IngredientCountRequest.created_at.desc(), IngredientCountRequest.id.desc())
        .limit(1)
    ).first()
    return waiting or latest(db, outlet_id, period_start)


def pending_outlet_ids(db: Session, outlet_ids: list[str]) -> set[str]:
    """Cabang di antara ini yang punya pengajuan menunggu, untuk ditandai di layar lain."""
    if not outlet_ids:
        return set()
    return set(db.scalars(select(IngredientCountRequest.outlet_id).where(IngredientCountRequest.outlet_id.in_(outlet_ids), IngredientCountRequest.status == REQUEST_PENDING)))


def pending_page(db: Session, outlet_id: str | None, page: int, size: int) -> tuple[list[IngredientCountRequest], int]:
    """Pengajuan yang menunggu, terlama dulu supaya yang paling lama menunggu diputus lebih dulu; tanpa cabang berarti semua cabang."""
    filters = [IngredientCountRequest.status == REQUEST_PENDING]
    if outlet_id:
        filters.append(IngredientCountRequest.outlet_id == outlet_id)
    total = db.scalar(select(func.count()).select_from(IngredientCountRequest).where(*filters)) or 0
    rows = db.scalars(
        select(IngredientCountRequest).where(*filters).order_by(IngredientCountRequest.created_at.asc(), IngredientCountRequest.id).offset((page - 1) * size).limit(size)
    ).all()
    return list(rows), total


def get(db: Session, outlet_id: str | None, request_id: str) -> IngredientCountRequest:
    request = db.get(IngredientCountRequest, request_id)
    if request is None or (outlet_id and request.outlet_id != outlet_id):
        raise DomainError(REQUEST_NOT_FOUND, status=NOT_FOUND)
    return request


def mark_seen(db: Session, user: User, outlet_id: str | None, request_id: str) -> None:
    """Dicatat sekali saat admin pertama kali membuka pengajuan yang masih menunggu; tulis bersyarat supaya dua admin tidak saling menimpa."""
    request = get(db, outlet_id, request_id)
    db.execute(
        update(IngredientCountRequest)
        .where(IngredientCountRequest.id == request.id, IngredientCountRequest.status == REQUEST_PENDING, IngredientCountRequest.seen_at.is_(None))
        .values(seen_at=now(), seen_by=user.id)
    )
    db.commit()


def reject(db: Session, user: User, outlet_id: str | None, request_id: str) -> IngredientCountRequest:
    """Periode tetap berjalan dan stok tidak berubah; cabang bisa mengajukan lagi."""
    request = get(db, outlet_id, request_id)
    db.refresh(request, with_for_update=True)
    if request.status != REQUEST_PENDING:
        raise DomainError(ALREADY_DECIDED, status=CONFLICT)
    request.status = REQUEST_REJECTED
    request.decided_by = user.id
    request.decided_at = now()
    db.commit()
    return request


def settle(db: Session, user: User, outlet_id: str, count_id: str) -> None:
    """Dipanggil di transaksi yang sama dengan penutupan periode: pengajuan cabang yang menunggu ikut selesai."""
    db.execute(
        update(IngredientCountRequest)
        .where(IngredientCountRequest.outlet_id == outlet_id, IngredientCountRequest.status == REQUEST_PENDING)
        .values(status=REQUEST_CLOSED, decided_by=user.id, decided_at=now(), count_id=count_id)
    )
