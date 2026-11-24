"""HTTP surface of the busy-products report."""
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
from web.management.reports.menu.busy_products import service
from web.management.reports.menu.busy_products.constants import (
    PRODUCTS_PER_PAGE_DEFAULT,
    PRODUCTS_PER_PAGE_MAX,
    PRODUCTS_PER_PAGE_MIN,
    SEARCH_MAX_LENGTH,
    SERIES_DEFAULT,
    SERIES_MAX,
    SORT_PATTERN,
    SORT_QTY,
)
from web.management.reports.menu.busy_products.mappers import busy_products_out
from web.management.reports.menu.busy_products.schemas import BusyProductsOut
from web.management.reports.menu.constants import HOUR_DESCRIPTION, LAST_HOUR, UNIT_HOUR, UNIT_PATTERN
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(BusyProductsOut)


@router.get("/busy-products", response_model=BusyProductsOut)
def busy_products(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    unit: str = Query(UNIT_HOUR, pattern=UNIT_PATTERN, description="Unit of the time axis"),
    hour: int | None = Query(None, ge=0, le=LAST_HOUR, description=HOUR_DESCRIPTION),
    search: str | None = Query(None, max_length=SEARCH_MAX_LENGTH, description="Filters product names"),
    sort: str = Query(SORT_QTY, pattern=SORT_PATTERN),
    series: int = Query(SERIES_DEFAULT, ge=1, le=SERIES_MAX, description="How many products the chart draws"),
    page: int = Query(1, ge=1),
    per_page: int = Query(PRODUCTS_PER_PAGE_DEFAULT, ge=PRODUCTS_PER_PAGE_MIN, le=PRODUCTS_PER_PAGE_MAX),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.BUSY_PRODUCTS)),
):
    """What sells and when, one row per product and time slot."""
    try:
        # Free text has no end of values, so it is never a key.
        if (search or "").strip():
            return busy_products_out(
            service.busy_products(db, start, end, unit, hour, search, sort, series, page, per_page, outlet_id)
        )
        return cache.read("web.reports.busy-products", (start, end, unit, hour, sort, series, page, per_page, outlet_id), lambda: busy_products_out(
            service.busy_products(db, start, end, unit, hour, search, sort, series, page, per_page, outlet_id)
        ), SHAPE, cache.REPORT_SECONDS)
    except DomainError as error:
        raise as_http(error) from error
