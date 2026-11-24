"""Requests to close a branch's stock count period, asked from the tablet and decided here; the rules live in app.core.ingredient_count_requests."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.ingredients import count_requests
from app.core.ingredients import counts
from app.core.ingredients import openings
from app.core.auth import readable_outlet_id, require_gate, require_permission, writable_outlet_id
from app.core.branches import outlet_names
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.user_names import user_names
from app.models.ingredient import Ingredient, IngredientCount, IngredientCountRequest
from app.models.user import User
from web.management.ingredient_counts.constants import PERMISSION_COUNT, PERMISSION_REQUEST, SHEET_GATE
from web.management.ingredient_count_requests.schemas import IngredientCountRequestIn, IngredientCountRequestOut, IngredientCountRequestPageOut

router = APIRouter(prefix="/ingredient-count-requests", tags=["web-ingredient-count-requests"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _opening_progress(db: Session, outlet_id: str, start: date) -> tuple[int, int]:
    """Bahan aktif cabang ini, dan berapa dari situ yang stok awal periode `start`-nya sudah diisi; sama seperti GET .../opening-period, dua query per cabang, tanpa N+1 per bahan."""
    active = [Ingredient.outlet_id == outlet_id, Ingredient.is_active.is_(True)]
    total = db.scalar(select(func.count()).select_from(Ingredient).where(*active)) or 0
    filled = db.scalar(select(func.count()).select_from(Ingredient).where(*active, openings.has_opening(start, Ingredient.id))) or 0
    return int(total), int(filled)


def _out(db: Session, rows: list[IngredientCountRequest]) -> list[IngredientCountRequestOut]:
    branches = outlet_names(db, (row.outlet_id for row in rows))
    names = user_names(db, [row.requested_by for row in rows] + [row.decided_by for row in rows] + [row.seen_by for row in rows])
    progress = {(row.outlet_id, row.period_start): _opening_progress(db, row.outlet_id, row.period_start) for row in rows}
    closed = {count.id: (count.period_start, count.period_end) for count in db.scalars(select(IngredientCount).where(IngredientCount.id.in_([row.count_id for row in rows if row.count_id]))).all()}
    upcoming = {outlet_id: counts.closing_period(db, outlet_id) for outlet_id in {row.outlet_id for row in rows if row.count_id not in closed}}
    return [
        IngredientCountRequestOut(
            id=row.id,
            outlet_id=row.outlet_id,
            outlet_name=branches.get(row.outlet_id, ""),
            period_start=row.period_start,
            status=row.status,
            note=row.note,
            requested_by=names.get(row.requested_by) if row.requested_by else None,
            decided_by=names.get(row.decided_by) if row.decided_by else None,
            decided_at=row.decided_at,
            seen_by=names.get(row.seen_by) if row.seen_by else None,
            seen_at=row.seen_at,
            count_id=row.count_id,
            created_at=row.created_at,
            close_start=(closed.get(row.count_id) or upcoming[row.outlet_id])[0],
            close_end=(closed.get(row.count_id) or upcoming[row.outlet_id])[1],
            opening_total=progress[(row.outlet_id, row.period_start)][0],
            opening_filled=progress[(row.outlet_id, row.period_start)][1],
        )
        for row in rows
    ]


@router.get("", response_model=IngredientCountRequestPageOut)
def list_waiting(
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_COUNT)),
):
    """Waiting requests, oldest first; never cached, the screen reloads on live signals."""
    rows, total = count_requests.pending_page(db, outlet_id, page, size)
    return IngredientCountRequestPageOut(items=_out(db, rows), total=total, page=page, size=size)


@router.get("/current", response_model=IngredientCountRequestOut | None)
def current_request(
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(SHEET_GATE)),
):
    """Pengajuan terakhir cabang ini beserta keputusannya; tidak di-cache karena berubah begitu diajukan, dilihat, atau diputus."""
    request = count_requests.current(db, outlet_id)
    return _out(db, [request])[0] if request else None


@router.post("", response_model=IngredientCountRequestOut, status_code=status.HTTP_201_CREATED)
def submit_request(
    body: IngredientCountRequestIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_REQUEST)),
):
    """Jalur yang sama dengan tombol Ajukan di tablet; admin pemegang stok.opname yang menutup periodenya."""
    try:
        request = count_requests.submit(db, user, outlet_id, body.note)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return _out(db, [request])[0]


@router.get("/{request_id}", response_model=IngredientCountRequestOut)
def get_request(
    request_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_COUNT)),
):
    try:
        row = count_requests.get(db, outlet_id, request_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return _out(db, [row])[0]


@router.post("/{request_id}/seen", status_code=status.HTTP_204_NO_CONTENT)
def mark_seen(
    request_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_COUNT)),
):
    """Dipanggil halaman pengajuan saat dibuka admin; pengajuan yang sudah dilihat atau sudah diputus tidak berubah."""
    try:
        count_requests.mark_seen(db, user, outlet_id, request_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{request_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
def reject_request(
    request_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_COUNT)),
):
    try:
        count_requests.reject(db, user, outlet_id, request_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
