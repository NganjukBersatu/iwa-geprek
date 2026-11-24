"""HTTP surface of the money trail; rows are written only by database triggers, every reading rule lives in app.core.finance.money_changes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.finance import money_changes
from app.core.finance.money_changes import MoneyChangePageOut, MoneyChangeReportOut
from app.core.finance.session_control import PERMISSION_VIEW_ALL
from app.models.money_change import MoneySubject
from app.models.user import User
from web.management.reports.common import month_to_date

router = APIRouter(prefix="/money-changes", tags=["web-money-changes"])

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


# Not cached: the triggers write these rows without passing through the app, so no table version would ever mark them stale.
@router.get("", response_model=MoneyChangeReportOut)
def list_changes(
    start: Day | None = Query(None, description="Both empty means the month so far"),
    end: Day | None = Query(None),
    subject: MoneySubject | None = Query(None),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    try:
        first, last = month_to_date(start, end)
        return money_changes.page_of(db, first, last, outlet_id, subject, sort, page, size)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("/sessions/{session_id}", response_model=MoneyChangePageOut)
def session_changes(
    session_id: str,
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    try:
        return money_changes.of_session(db, session_id, outlet_id, sort, page, size)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
