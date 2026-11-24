"""HTTP surface of the turnover report."""
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
from web.management.reports.common import as_http, last_days
from web.management.reports.inventory.constants import DORMANT_DAYS
from web.management.reports.inventory.stock_turnover import service
from web.management.reports.inventory.stock_turnover.domain import SLOW_DAYS, TARGET_DAYS, URGENT_DAYS, Thresholds
from web.management.reports.inventory.stock_turnover.mappers import turnover_out
from web.management.reports.inventory.stock_turnover.schemas import TurnoverOut
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(TurnoverOut)

# A short default month on the 1st would make the usage pace misleading, so turnover looks back a fixed span.
TURNOVER_DEFAULT_DAYS = 30
MAX_PLAN_DAYS = 180
MAX_IDLE_DAYS = 365


@router.get("/stock-turnover", response_model=TurnoverOut)
def stock_turnover(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    target_days: int = Query(TARGET_DAYS, ge=1, le=MAX_PLAN_DAYS, description="Suggested purchases cover this many days ahead"),
    urgent_days: int = Query(URGENT_DAYS, ge=1, le=MAX_PLAN_DAYS, description="Stock lasting fewer days is marked urgent"),
    dormant_days: int = Query(DORMANT_DAYS, ge=1, le=MAX_IDLE_DAYS, description="Stock unmoved this long is marked dormant"),
    slow_days: int = Query(SLOW_DAYS, ge=1, le=MAX_IDLE_DAYS, description="Stock lasting more days is marked slow"),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.STOCK_TURNOVER)),
):
    """How fast each ingredient moves, when it runs out, and how much to buy; defaults to the last 30 days."""
    try:
        start, end = last_days(start, end, TURNOVER_DEFAULT_DAYS)
    except DomainError as error:
        raise as_http(error) from error
    thresholds = Thresholds(
        target_days=target_days, urgent_days=urgent_days, dormant_days=dormant_days, slow_days=slow_days
    )
    return cache.read(
        "web.reports.stock-turnover",
        (start, end, target_days, urgent_days, dormant_days, slow_days, outlet_id, sort),
        lambda: turnover_out(service.sorted_report(service.turnover_report(db, outlet_id, start, end, thresholds), sort)),
        SHAPE,
        cache.REPORT_SECONDS,
    )
