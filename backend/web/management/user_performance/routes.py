"""HTTP surface of the admin's user performance; every rule lives in the service."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_permission
from app.core.clock import now
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.sorting import RowSorting, Sort
from app.employee.performance.domain import Range
from app.models.user import User
from web.management.user_performance import service
from web.management.user_performance.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, PERMISSION_VIEW
from web.management.user_performance.mappers import detail_out, row_out
from web.management.user_performance.schemas import ListRange, UserPerformanceOut, UserPerformancePageOut, UserPerformanceRowOut

router = APIRouter(prefix="/user-performance", tags=["v2-user-performance"])
viewer = require_permission(PERMISSION_VIEW)

SORTING: RowSorting[UserPerformanceRowOut] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "role": lambda row: row.role_name,
        "outlet": lambda row: row.outlet_name,
        "stars": lambda row: row.stars,
        "on_time": lambda row: row.on_time_percent,
        "late": lambda row: row.late,
        "absent": lambda row: row.absent,
        "work": lambda row: row.work_minutes,
        "overtime": lambda row: row.overtime_minutes,
        "tasks": lambda row: row.tasks_done,
    },
    identity=lambda row: row.user_id,
)


def _lowest_first(row: UserPerformanceRowOut) -> tuple[bool, float, str, str]:
    """Urutan bawaan: bintang terendah di atas karena merekalah yang perlu perhatian; tanpa bintang di bawah."""
    return (row.stars is None, row.stars or 0.0, row.name.casefold(), row.user_id)


# Tanpa cache: nilainya bergantung pada jam sekarang (tugas yang lewat batas waktu, hari yang sudah lewat), bukan hanya pada tabel yang dibaca.
@router.get("", response_model=UserPerformancePageOut)
def list_performance(
    range: ListRange = Query(ListRange.CYCLE, description="cycle or previous; each person's own pay cycle"),
    search: str | None = Query(None, max_length=100, description="Part of the name or username"),
    outlet_id: str | None = Depends(readable_outlet_id),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(viewer),
):
    """Every active employee over their own cycle, the same numbers the app shows them."""
    rows = [row_out(measured) for measured in service.everyone(db, outlet_id, search, Range(range.value), now())]
    try:
        ordered = SORTING.apply(rows, sort) if sort else sorted(rows, key=_lowest_first)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    start = (page - 1) * size
    return UserPerformancePageOut(items=ordered[start : start + size], total=len(ordered), page=page, size=size)


# Tanpa cache, dengan alasan yang sama dengan daftarnya.
@router.get("/{user_id}", response_model=UserPerformanceOut)
def read_performance(
    user_id: str,
    range: Range = Query(Range.CYCLE, description="cycle, previous, or all"),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(viewer),
):
    """One employee, exactly what their Performance page in the app shows."""
    try:
        return detail_out(service.one(db, user_id, outlet_id, range, now()))
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
