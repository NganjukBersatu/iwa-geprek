"""HTTP surface of the stock count; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache
from app.core.ingredients import count_drafts as drafts
from app.core.ingredients import count_requests
from app.core.ingredients import counts
from app.core.ingredients import openings
from app.core.auth import readable_outlet_id, require_gate, require_permission, writable_outlet_id
from app.core.branches import outlet_name, outlet_names, outlets_in_scope
from app.core.clock import today as clock_today
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.ingredients import messages as core_messages
from app.core.sorting import Sort
from app.models.ingredient import IngredientCount
from app.models.user import User
from web.management.ingredient_counts import repository, service
from web.management.ingredient_counts.constants import SHEET_GATE, CHANGES_MAX_PAGE_SIZE, CHANGES_PAGE_SIZE, DEFAULT_LIMIT, MAX_LIMIT, PERMISSION_CORRECT, PERMISSION_COUNT, PERMISSION_VIEW
from web.management.ingredient_counts.domain import CountDraft, CountLine
from web.management.ingredient_counts.schemas import ClosingPeriodOut, OpeningStatusOut, CountChangeOut, CountChangePageOut, CountCloseIn, CountDetailOut, CountDraftIn, CountDraftOut, CountLinesIn, CountOut, DraftLineOut, OpeningIn, OpenSessionsOut, RunningCountOut
from web.management.reports.inventory.ingredient_stock import service as stock
from web.management.reports.inventory.ingredient_stock.mappers import ingredient_stock_out
from web.management.reports.inventory.ingredient_stock.schemas import IngredientStockOut

router = APIRouter(prefix="/ingredient-counts", tags=["web-ingredient-counts"])

SHEET = TypeAdapter(IngredientStockOut)
COUNTS = TypeAdapter(list[CountOut])
DETAIL = TypeAdapter(CountDetailOut)


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _out(count: IngredientCount, user_name: str | None, total: int, branch_name: str) -> CountOut:
    return CountOut(id=count.id, outlet_id=count.outlet_id, outlet_name=branch_name, start=count.period_start, end=count.period_end, note=count.note, user_name=user_name, ingredient_count=total, source=count.source, created_at=count.created_at)


def _detail(db: Session, count_id: str, part: counts.OpenPiece | None = None) -> CountDetailOut:
    count, name, total = repository.summary_of(db, count_id)
    start, end = (part.start, part.end) if part and part.end else (count.period_start, count.period_end)
    report = ingredient_stock_out(stock.stock_report(db, count.outlet_id, start, end))
    base = _out(count, name, 0 if part else total, outlet_name(db, count.outlet_id) or "").model_copy(update={"start": start, "end": end})
    return CountDetailOut(**base.model_dump(), report=report, own_period=part is None)


@router.get("/running", response_model=list[RunningCountOut])
def running_counts(
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """Waktu yang belum ditutup per cabang dipotong menurut periode cabang, ditambah bagian yang sudah masuk stok awal sebuah penutupan; tidak di-cache karena berubah begitu periode ditutup."""
    branches = outlets_in_scope(db, outlet_id)
    pieces = counts.open_pieces(db, branches)
    absorbed = counts.absorbed_pieces(db, branches)
    requested = count_requests.pending_outlet_ids(db, [branch.id for branch in branches])
    today_ = clock_today()
    rows: list[RunningCountOut] = []
    for branch in branches:
        own = pieces.get(branch.id, [])
        # Pengajuan tablet menyangkut periode yang ditutup berikutnya: baris Perlu ditutup, atau baris berjalan bila tidak ada.
        asks = next((piece for piece in own if piece.state == counts.OpenState.TO_CLOSE), own[0] if own else None)
        rows.extend(
            RunningCountOut(
                outlet_id=branch.id,
                outlet_name=branch.name,
                start=piece.start,
                end=piece.end,
                state=piece.state,
                period_start=piece.period_start,
                period_end=piece.period_end,
                days=((piece.end or today_) - piece.start).days + 1,
                requested=branch.id in requested and piece is asks,
            )
            for piece in [*own, *absorbed.get(branch.id, [])]
        )
    return rows


@router.get("/draft", response_model=CountDraftOut)
def read_draft(
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_COUNT)),
):
    """The counted figures typed for this branch and not closed yet; never cached, since another screen may have just written one."""
    lines = [DraftLineOut(ingredient_id=entry.ingredient_id, counted=entry.counted, user_name=entry.user_name, updated_at=entry.updated_at) for entry in drafts.read(db, outlet_id)]
    return CountDraftOut(lines=lines)


@router.put("/draft", status_code=status.HTTP_204_NO_CONTENT)
def save_draft(
    body: CountDraftIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_COUNT)),
):
    with _domain_errors():
        drafts.save(db, user, outlet_id, [drafts.DraftLine(line.ingredient_id, line.counted) for line in body.lines])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/opening-status", response_model=OpeningStatusOut)
def opening_status(
    outlet_id: str = Depends(writable_outlet_id),
    start: date | None = Query(None, description="Hari pertama periode di lembar opname; kosong berarti periode berjalan."),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(SHEET_GATE)),
):
    """Sama dengan hitungan "Stok awal terisi" di tablet; tidak di-cache karena berubah setiap stok awal diisi atau periode ditutup."""
    status = openings.fill_status(db, outlet_id, start)
    return OpeningStatusOut(start=status.start, filled=status.filled, total=status.total, missing_ids=status.missing_ids)


@router.get("/closing-period", response_model=ClosingPeriodOut)
def closing_period(
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(SHEET_GATE)),
):
    """Rentang yang dipilih otomatis saat menutup periode; tidak di-cache karena berubah begitu periode ditutup atau periode cabang diubah."""
    with _domain_errors():
        start, end = counts.closing_period(db, outlet_id)
    return ClosingPeriodOut(start=start, end=end)


@router.get("/open-sessions", response_model=OpenSessionsOut)
def open_sessions(
    end: date = Query(...),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(SHEET_GATE)),
):
    """Sesi kasir yang menghalangi penutupan; tidak di-cache karena sesi bisa ditutup kapan saja dan layar harus langsung tahu."""
    return OpenSessionsOut(count=counts.open_sessions(db, outlet_id, end))


@router.get("/sheet", response_model=IngredientStockOut)
def sheet(
    start: date = Query(...),
    end: date = Query(...),
    sort: Sort = None,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(SHEET_GATE)),
):
    """The worksheet: the system column is filled and only the physical count is left to type, with the same figures the report shows."""
    if end < start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=core_messages.END_BEFORE_START)
    return cache.read(
        "web.ingredient-counts.sheet",
        (outlet_id, start, end, sort),
        lambda: ingredient_stock_out(stock.sorted_report(stock.stock_report(db, outlet_id, start, end), sort)),
        SHEET,
        cache.LIST_SECONDS,
    )


@router.get("", response_model=list[CountOut])
def list_counts(
    sort: Sort = None,
    source: str | None = Query(None, pattern="^(web|tablet)$", description="Only the counts closed from this place"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    def build() -> list[CountOut]:
        counts = repository.list_counts(db, outlet_id, sort, limit, source)
        names = outlet_names(db, [count.outlet_id for count, _, _ in counts])
        return [_out(count, name, total, names.get(count.outlet_id, "")) for count, name, total in counts]

    return cache.read("web.ingredient-counts", (outlet_id, sort, limit, source), build, COUNTS, cache.LIST_SECONDS)


@router.post("", response_model=CountDetailOut, status_code=status.HTTP_201_CREATED)
def close_count(
    body: CountCloseIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_COUNT)),
):
    draft = CountDraft(body.start, body.end, body.note, [CountLine(line.ingredient_id, line.counted) for line in body.lines])
    with _domain_errors():
        count = service.close(db, user, outlet_id, draft)
    return _detail(db, count.id)


@router.get("/{count_id}", response_model=CountDetailOut)
def count_detail(
    count_id: str,
    part_start: date | None = Query(None, description="Hari pertama bagian waktu yang ikut tertutup sebagai stok awal opname ini; kosong berarti periode opname itu sendiri."),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    def build() -> CountDetailOut:
        with _domain_errors():
            service.get(db, outlet_id, count_id)
            part = service.part_of(db, outlet_id, count_id, part_start) if part_start else None
        return _detail(db, count_id, part)

    return cache.read("web.ingredient-counts.detail", (outlet_id, count_id, part_start), build, DETAIL, cache.LIST_SECONDS)


@router.delete("/{count_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_count(
    count_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_CORRECT)),
):
    with _domain_errors():
        service.cancel(db, outlet_id, count_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{count_id}/lines", response_model=CountDetailOut)
def set_lines(
    count_id: str,
    body: CountLinesIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_CORRECT)),
):
    """Mengoreksi jumlah real sebuah hitungan yang sudah ditutup; stok tetap seperti adanya."""
    with _domain_errors():
        service.set_lines(db, user, outlet_id, count_id, [CountLine(line.ingredient_id, line.counted) for line in body.lines])
    return _detail(db, count_id)


@router.get("/{count_id}/changes", response_model=CountChangePageOut)
def count_changes(
    count_id: str,
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(CHANGES_PAGE_SIZE, ge=1, le=CHANGES_MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """Siapa mengubah jumlah real mana pada hitungan ini, terbaru dulu; tidak di-cache supaya koreksi langsung terlihat."""
    with _domain_errors():
        service.get(db, outlet_id, count_id)
    rows, total = repository.changes_page(db, count_id, sort, page, size)
    items = [
        CountChangeOut(
            id=change.id,
            ingredient_id=change.ingredient_id,
            ingredient_name=change.ingredient_name,
            action=change.action,
            old_counted=change.old_counted,
            new_counted=change.new_counted,
            user_name=name,
            created_at=change.created_at,
        )
        for change, name in rows
    ]
    return CountChangePageOut(items=items, total=total, page=page, size=size)


opening_bulk = APIRouter(prefix="/opening")
bulk.add_bulk_routes(
    opening_bulk,
    PERMISSION_COUNT,
    create_schema=OpeningIn,
    create=lambda db, body, user, outlet_id: service.set_opening(db, user, outlet_id, body.ingredient_id, body.opening, body.from_date),
    create_context=writable_outlet_id,
)
router.include_router(opening_bulk)
