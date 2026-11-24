"""HTTP surface of the customer report, rebuilt from the legacy /laporan routes."""
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
from web.management.reports import gates
from web.management.reports.sales.customers import service
from web.management.reports.sales.customers.constants import DEFAULT_CUSTOMERS_PAGE_SIZE, MAX_CUSTOMERS_PAGE_SIZE
from web.management.reports.sales.customers.mappers import customer_report_out
from web.management.reports.sales.customers.schemas import CustomerReportOut

router = APIRouter(prefix="/reports/customers", tags=["v2-reports"])

SHAPE = TypeAdapter(CustomerReportOut)


@router.get("", response_model=CustomerReportOut)
def customers(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    search: str | None = Query(None, description="Customer name"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_CUSTOMERS_PAGE_SIZE, ge=1, le=MAX_CUSTOMERS_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.CUSTOMERS)),
):
    """Who came in the range, latest visitor first."""
    try:
        # Free text has no end of values, so it is never a key.
        if (search or "").strip():
            return customer_report_out(service.customer_report(db, start, end, outlet_id, search, page, size))
        return cache.read(
            "web.reports.customers",
            (start, end, page, size, outlet_id),
            lambda: customer_report_out(service.customer_report(db, start, end, outlet_id, search, page, size)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
