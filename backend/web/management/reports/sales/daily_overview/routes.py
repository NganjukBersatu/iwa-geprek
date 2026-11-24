"""HTTP surface of the daily overview, rebuilt from the legacy /laporan routes."""
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
from web.management.reports.sales.daily_overview import service
from web.management.reports.sales.daily_overview.mappers import daily_overview_out
from web.management.reports.sales.daily_overview.schemas import DailyOverviewOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/daily-overview", tags=["v2-reports"])

SHAPE = TypeAdapter(DailyOverviewOut)


@router.get("", response_model=DailyOverviewOut)
def daily_overview(
    start: Day | None = Query(None, description="Both empty means the month so far"),
    end: Day | None = Query(None),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.OVERVIEW)),
):
    """Cash and non-cash income, expense, and profit per business day."""
    try:
        return cache.read(
            "web.reports.daily-overview",
            (start, end, outlet_id),
            lambda: daily_overview_out(service.daily_overview(db, start, end, outlet_id)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
