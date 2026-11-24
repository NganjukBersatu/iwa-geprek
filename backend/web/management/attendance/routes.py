"""HTTP surface of the admin's attendance screens; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.date_range import Bound
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.models.attendance import AttendanceStatus
from app.models.user import User
from web.management.attendance import service
from web.management.attendance.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, PERMISSION_MANAGE
from web.management.attendance.domain import AttendanceChanges, AttendanceFilter, MarkDraft
from web.management.attendance.mappers import attendance_list_out, attendance_out, attendance_page_out
from web.management.attendance.schemas import AttendanceOut, AttendancePageOut, EditIn, MarkIn
from app.core.sorting import Sort

router = APIRouter(prefix="/attendance", tags=["v2-attendance-manage"])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _filter(
    start: Bound | None,
    end: Bound | None,
    user_id: str | None,
    attendance_status: AttendanceStatus | None,
    has_photo: bool | None,
    outside_schedule: bool | None,
    search: str | None,
    outlet_id: str | None,
) -> AttendanceFilter:
    return AttendanceFilter(
        start=start, end=end, user_id=user_id, status=attendance_status, has_photo=has_photo,
        outside_schedule=outside_schedule, search=search.strip() if search else None, outlet_id=outlet_id,
    )


@router.get("", response_model=AttendancePageOut)
def list_attendance(
    start: Bound | None = Query(None, description="YYYY-MM-DD, or with a clock time to match the hours worked inside the range"),
    end: Bound | None = Query(None),
    user_id: str | None = Query(None),
    attendance_status: AttendanceStatus | None = Query(None, alias="status"),
    has_photo: bool | None = Query(None),
    outside_schedule: bool | None = Query(None),
    search: str | None = Query(None, description="Part of the name or the username"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    filter = _filter(start, end, user_id, attendance_status, has_photo, outside_schedule, search, outlet_id)
    return attendance_page_out(service.list_page(db, filter, sort, page, size), public_base_url())


@router.get("/range", response_model=list[AttendanceOut])
def attendance_in_range(
    start: Bound | None = Query(None, description="Default: Monday of the week"),
    end: Bound | None = Query(None, description="Default: six days after the start"),
    user_id: str | None = Query(None),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """For the schedule board: every record of a short range at once, without paging."""
    filter = _filter(start, end, user_id, None, None, None, None, outlet_id)
    with _domain_errors():
        return attendance_list_out(service.list_range(db, filter), public_base_url())


@router.post("/mark", response_model=AttendanceOut)
def mark_attendance(
    body: MarkIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    draft = MarkDraft(**body.model_dump())
    with _domain_errors():
        return attendance_out(service.mark(db, admin, draft), public_base_url())


@router.get("/{record_id}", response_model=AttendanceOut)
def get_attendance(
    record_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return attendance_out(service.get(db, admin, record_id), public_base_url())


@router.patch("/{record_id}", response_model=AttendanceOut)
def edit_attendance(
    record_id: str,
    body: EditIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    given = frozenset(body.model_fields_set)
    changes = AttendanceChanges(given=given, **body.model_dump())
    with _domain_errors():
        return attendance_out(service.edit(db, admin, record_id, changes), public_base_url())


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    record_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, admin, record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
