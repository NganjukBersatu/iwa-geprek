"""HTTP surface of the busy-sales report."""
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
from web.management.reports.menu.busy_sales import service
from web.management.reports.menu.busy_sales.mappers import busy_sales_out
from web.management.reports.menu.busy_sales.schemas import BusySalesOut
from web.management.reports.menu.constants import HOUR_DESCRIPTION, LAST_HOUR, UNIT_HOUR, UNIT_PATTERN
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(BusySalesOut)


@router.get("/busy-sales", response_model=BusySalesOut)
def busy_sales(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    unit: str = Query(UNIT_HOUR, pattern=UNIT_PATTERN, description="Unit of the time axis"),
    hour: int | None = Query(None, ge=0, le=LAST_HOUR, description=HOUR_DESCRIPTION),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.BUSY_SALES)),
):
    """When the shop is busy, the whole shop per time slot."""
    try:
        return cache.read(
            "web.reports.busy-sales",
            (start, end, unit, hour, outlet_id, sort),
            lambda: busy_sales_out(service.busy_sales(db, start, end, unit, hour, outlet_id), sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
