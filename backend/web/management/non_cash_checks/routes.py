"""HTTP surface of the non-cash checks (QC against the bank app), rebuilt from the legacy /validasi-nontunai routes."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate, require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import RowSorting, Sort
from app.models.user import User
from web.management.non_cash_checks import service
from web.management.non_cash_checks.constants import PERMISSION_WRITE
from web.management.non_cash_checks.schemas import NonCashCheckIn, NonCashCheckRowOut, NonCashChecksOut
from web.management.reports.common import as_http
from web.management.reports import gates

router = APIRouter(prefix="/non-cash-checks", tags=["web-non-cash-checks"])

CHECKS = TypeAdapter(NonCashChecksOut)

SORTING: RowSorting[NonCashCheckRowOut] = RowSorting(
    keys={
        "date": lambda row: row.date,
        "outlet": lambda row: row.outlet_name,
        "recorded": lambda row: row.recorded,
        "bank_amount": lambda row: row.bank_amount,
        "difference": lambda row: row.difference,
    },
    identity=lambda row: f"{row.date.isoformat()}:{row.outlet_id}",
)



def _sorted(report: NonCashChecksOut, sort: str | None) -> NonCashChecksOut:
    return report.model_copy(update={"rows": SORTING.apply(report.rows, sort)})

@router.get("", response_model=NonCashChecksOut)
def list_checks(
    start: Day | None = Query(None, description="Both empty means the month so far"),
    end: Day | None = Query(None),
    status: Literal["all", "pending", "balanced", "mismatch"] = Query("all"),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.OVERVIEW)),
):
    """Recorded non-cash money against the bank figure per day: for one branch, or a row per branch for each day when none is given."""
    try:
        return cache.read(
            "web.non-cash-checks",
            (start, end, status, outlet_id, sort),
            lambda: _sorted(service.checks(db, start, end, status, outlet_id), sort),
            CHECKS,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error


@router.put("/{day}", response_model=NonCashCheckRowOut)
def save_check(
    day: date,
    body: NonCashCheckIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_WRITE)),
):
    """Fills or replaces the bank figure of one day."""
    try:
        return service.save(db, day, body.bank_amount, outlet_id, user.id)
    except DomainError as error:
        raise as_http(error) from error


@router.delete("/{day}", status_code=status.HTTP_204_NO_CONTENT)
def clear_check(
    day: date,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_WRITE)),
):
    """Empties the check of one day; it goes back to pending."""
    service.clear(db, day, outlet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
