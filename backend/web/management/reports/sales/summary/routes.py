"""HTTP surface of the summary, rebuilt from the legacy /laporan routes."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.models.user import User
from web.management.reports.common import as_http
from web.management.reports.sales.summary import service
from web.management.reports.sales.summary.mappers import summary_out
from web.management.reports.sales.summary.schemas import SalesSummaryOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/summary", tags=["v2-reports"])

SHAPE = TypeAdapter(SalesSummaryOut)


@router.get("", response_model=SalesSummaryOut)
def summary(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.SUMMARY)),
):
    """Sales, expenses, and visitors of one range in one call."""
    try:
        return cache.read(
            "web.reports.summary",
            (start, end, outlet_id),
            lambda: summary_out(service.summary(db, start, end, outlet_id)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
