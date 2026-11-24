"""HTTP surface of the admin's batches; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_permission, writable_outlet_id
from app.core.branches import outlet_name, outlet_names
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.core.sorting import Sort
from app.models.user import User
from web.management.batches import history, service
from web.management.batches.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MAX_SEARCH_LENGTH, PERMISSION_MANAGE
from web.management.batches.domain import BatchDraft, ItemDraft, RunQuery
from web.management.batches.mappers import copy_out, managed_list_out, managed_out, run_detail_out, run_page_out, shift_code_list_out, user_page_out
from web.management.batches.schemas import (
    BatchCopyIn,
    BatchCopyOut,
    BatchIn,
    BatchShiftCodeListOut,
    BatchUserPageOut,
    ManagedBatchListOut,
    ManagedBatchOut,
    RunDetailOut,
    RunPageOut,
)

router = APIRouter(prefix="/batches", tags=["v2-batches-manage"])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _draft(body: BatchIn) -> BatchDraft:
    return BatchDraft(
        name=body.name,
        start_clock=body.start_clock,
        end_clock=body.end_clock,
        is_active=body.is_active,
        items=tuple(ItemDraft(label=item.label, kind=item.kind, required=item.required, id=item.id) for item in body.items),
        kind=body.kind,
        fill_mode=body.fill_mode,
        shift_code_ids=tuple(body.shift_code_ids),
        repeat_unit=body.repeat_unit,
        repeat_every=body.repeat_every,
        starts_on=body.starts_on,
        target=body.target,
        user_ids=tuple(body.user_ids),
    )


@router.get("", response_model=ManagedBatchListOut)
def list_batches(
    kind: str | None = Query(None, description="outlet or routine; empty means both"),
    q: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Words in the task name or an item label"),
    active: bool | None = Query(None, description="true or false; empty means both"),
    repeat: str | None = Query(None, description="day, week, or month"),
    fill_mode: str | None = Query(None, description="one or each"),
    shift_code_id: str | None = Query(None, description="Only routine tasks attached to this shift code"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Tidak di-cache: daftar kelola yang dibuka sesekali, dan harus langsung memuat perubahan templat."""
    with _domain_errors():
        query = service.batch_query(outlet_id, kind, q, active, repeat, fill_mode, shift_code_id)
        batches, total = service.list_batches(db, query, sort, page, size)
    return managed_list_out(batches, outlet_names(db, [batch.outlet_id for batch in batches]), total, page, size)


@router.get("/shift-code-options", response_model=BatchShiftCodeListOut)
def shift_code_options(
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Tidak di-cache: kecil, dibuka hanya saat form tugas rutin dibuka, dan harus mengikuti kode shift terbaru."""
    return shift_code_list_out(service.shift_code_options(db, outlet_id))


@router.get("/user-options", response_model=BatchUserPageOut)
def user_options(
    q: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Words in the name or username"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Tidak di-cache: dibuka hanya saat memilih penerima, dan harus mengikuti karyawan aktif terbaru."""
    people, total = service.user_options(db, outlet_id, q, page, size)
    return user_page_out(people, total, page, size)


@router.post("/copies", response_model=BatchCopyOut)
def copy_batch(
    body: BatchCopyIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        outcomes = service.copy_batch(db, user, body.batch_id, body.outlet_ids)
    return copy_out(outcomes, outlet_names(db, [outcome.outlet_id for outcome in outcomes]))


@router.get("/runs", response_model=RunPageOut)
def list_runs(
    date_from: date | None = Query(None, description="First day, inclusive; with no date at all the list is this month"),
    date_to: date | None = Query(None, description="Last day, inclusive"),
    kind: str | None = Query(None, description="outlet or routine; empty means both"),
    q: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Words in the task name or the name of who filled it"),
    problems: bool | None = Query(None, description="true: only runs with a problem answer; false: only those without"),
    batch_id: str | None = Query(None, description="Only the runs of this task"),
    follow_up: str | None = Query(None, description="none: no follow-up task yet; open: one still unfinished; done: all finished"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Tidak di-cache: riwayat berubah tiap ada pengisian, dan live outlet_batch_runs memicu muat ulang."""
    with _domain_errors():
        first, last = history.day_window(date_from, date_to)
        wanted = RunQuery(
            first=first,
            last=last,
            outlet_id=outlet_id,
            kind=service.wanted_kind(kind),
            search=(q or "").strip() or None,
            problems=problems,
            batch_id=batch_id or None,
            follow_up=service.wanted_follow_up(follow_up),
        )
        return run_page_out(history.run_page(db, wanted, sort, page, size), page, size)


@router.get("/runs/{run_id}", response_model=RunDetailOut)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        run, answers, follow_ups, versions = history.run_detail(db, user, run_id)
        return run_detail_out(run, answers, follow_ups, versions, public_base_url())


@router.post("", response_model=ManagedBatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    body: BatchIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        batch = service.create_batch(db, outlet_id, _draft(body))
        return managed_out(batch, outlet_name(db, batch.outlet_id) or "")


@router.get("/{batch_id}", response_model=ManagedBatchOut)
def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        batch = service.get_batch(db, user, batch_id)
        return managed_out(batch, outlet_name(db, batch.outlet_id) or "")


@router.put("/{batch_id}", response_model=ManagedBatchOut)
def update_batch(
    batch_id: str,
    body: BatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        batch = service.update_batch(db, user, batch_id, _draft(body))
        return managed_out(batch, outlet_name(db, batch.outlet_id) or "")


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete_batch(db, user, batch_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
