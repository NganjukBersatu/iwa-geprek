"""HTTP surface of the cashier report, rebuilt from the legacy /laporan routes."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.models.user import User
from web.management.reports.common import as_http
from web.management.reports.sales.cashiers import service
from web.management.reports.sales.cashiers.mappers import cashier_report_out
from web.management.reports.sales.cashiers.schemas import CashierReportOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/cashiers", tags=["v2-reports"])

SHAPE = TypeAdapter(CashierReportOut)


@router.get("", response_model=CashierReportOut)
def cashiers(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.CASHIERS)),
):
    """Sales, purchases, and drawer difference per cashier; only cashiers active in the range appear."""
    try:
        return cache.read(
            "web.reports.cashiers",
            (start, end, outlet_id, sort),
            lambda: cashier_report_out(service.cashier_report(db, start, end, outlet_id), sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
