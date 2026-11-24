"""HTTP surface of the kitchen report."""
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
from web.management.reports.menu.kitchen import service
from web.management.reports.menu.kitchen.constants import KITCHEN_THRESHOLD_DEFAULT, KITCHEN_THRESHOLD_MAX
from web.management.reports.menu.kitchen.mappers import kitchen_out
from web.management.reports.menu.kitchen.schemas import KitchenOut
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(KitchenOut)


@router.get("/kitchen", response_model=KitchenOut)
def kitchen_times(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    threshold_minutes: int = Query(
        KITCHEN_THRESHOLD_DEFAULT, ge=1, le=KITCHEN_THRESHOLD_MAX, description="Longer than this counts as late"
    ),
    hour_sort: Sort = None,
    order_sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.STATION_PERFORMANCE)),
):
    """Serving time from order creation to the last board stage."""
    try:
        return cache.read(
            "web.reports.kitchen",
            (start, end, threshold_minutes, outlet_id, hour_sort, order_sort),
            lambda: kitchen_out(service.kitchen(db, start, end, threshold_minutes, outlet_id), hour_sort, order_sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
