"""HTTP surface of the trend, rebuilt from the legacy /laporan routes."""
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
from web.management.reports.sales.trend import service
from web.management.reports.sales.trend.constants import MAX_TREND_POINTS
from web.management.reports.sales.trend.domain import Period
from web.management.reports.sales.trend.mappers import trend_out
from web.management.reports.sales.trend.schemas import TrendOut, WindowOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/trend", tags=["v2-reports"])

SHAPE = TypeAdapter(TrendOut)


@router.get("/window", response_model=WindowOut)
def trend_window(
    period: Period = Query(Period.DAILY, description="daily, weekly, or monthly"),
    start: Day | None = Query(None, description="Start of a free range (WIB, inclusive); overrides period"),
    end: Day | None = Query(None, description="End of a free range; defaults to start"),
    _: User = Depends(require_gate(gates.DASHBOARD)),
):
    """Not cached: it is worked out from today's date in a few lines and holds no data of the business."""
    try:
        used, first, last = service.window(period, None, start, end)
    except DomainError as error:
        raise as_http(error) from error
    return WindowOut(period=used, start=first, end=last)


@router.get("", response_model=TrendOut)
def trend(
    period: Period = Query(Period.DAILY, description="daily, weekly, or monthly"),
    count: int | None = Query(None, ge=1, le=MAX_TREND_POINTS, description="Number of bars; defaults per period"),
    start: Day | None = Query(None, description="Start of a free range (WIB, inclusive); overrides period and count"),
    end: Day | None = Query(None, description="End of a free range; defaults to start"),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.TREND)),
):
    """Income, expense, and visitors per bar of the dashboard chart."""
    try:
        return cache.read(
            "web.reports.trend",
            (period.value, count, start, end, outlet_id),
            lambda: trend_out(service.trend(db, period, count, start, end, outlet_id)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
