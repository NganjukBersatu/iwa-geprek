"""HTTP surface of the comparison, rebuilt from the legacy /laporan routes."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.clock import today
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.models.user import User
from web.management.reports.common import as_http
from web.management.reports.sales.comparison import service
from web.management.reports.sales.comparison.domain import ComparisonMode
from web.management.reports.sales.comparison.mappers import comparison_out
from web.management.reports.sales.comparison.schemas import ComparisonOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/comparison", tags=["v2-reports"])

SHAPE = TypeAdapter(ComparisonOut)


@router.get("", response_model=ComparisonOut)
def comparison(
    start: Day = Query(...),
    end: Day = Query(...),
    mode: ComparisonMode = Query(ComparisonMode.AUTO, description="auto, week, month, year, or custom"),
    previous_start: Day | None = Query(None, description="Custom mode only"),
    previous_end: Day | None = Query(None, description="Custom mode only"),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.COMPARISON)),
):
    """This range against the comparable range before it."""
    try:
        # A range reaching today is cut at the current minute, which no table version tracks.
        if end >= today():
            return comparison_out(service.comparison(db, start, end, mode, previous_start, previous_end, outlet_id))
        return cache.read(
            "web.reports.comparison",
            (start, end, mode.value, previous_start, previous_end, outlet_id),
            lambda: comparison_out(service.comparison(db, start, end, mode, previous_start, previous_end, outlet_id)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
