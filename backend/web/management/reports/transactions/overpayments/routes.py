"""HTTP surface of the overpayment report; the report itself lives in app.core.finance.overpayment_report."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_full_access
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.finance import overpayment_report
from app.core.finance.overpayment_report import OverpaymentsOut
from app.models.user import User
from web.management.reports.common import as_http, from_today
from web.management.reports.transactions.paging import DEFAULT_PER_PAGE, MAX_PER_PAGE

router = APIRouter(prefix="/reports/overpayments", tags=["v2-reports"])

SHAPE = TypeAdapter(OverpaymentsOut)


@router.get("", response_model=OverpaymentsOut)
def overpayments(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    cashier_id: str | None = Query(None),
    method: str | None = Query(None, description="Payment method code"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_full_access),
):
    """Non-cash overpayments, newest first; read only."""
    try:
        first, last = from_today(start, end)
        return cache.read(
            "web.reports.overpayments",
            (start, end, cashier_id, method, sort, page, per_page, outlet_id),
            lambda: overpayment_report.report(db, first, last, outlet_id, cashier_id, method, sort, page, per_page),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
