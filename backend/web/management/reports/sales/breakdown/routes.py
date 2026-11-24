"""HTTP surface of the sales breakdown by order type and by branch."""
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
from web.management.reports import gates
from web.management.reports.common import as_http
from web.management.reports.sales.breakdown import service
from web.management.reports.sales.breakdown.mappers import sales_breakdown_out
from web.management.reports.sales.breakdown.schemas import SalesBreakdownOut

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(SalesBreakdownOut)


@router.get("/sales-breakdown", response_model=SalesBreakdownOut)
def sales_breakdown(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    type_sort: Sort = None,
    outlet_sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.BUSY_SALES)),
):
    """Sales per order type, and per branch while no branch is chosen."""
    try:
        return cache.read(
            "web.reports.sales-breakdown",
            (start, end, outlet_id, type_sort, outlet_sort),
            lambda: sales_breakdown_out(service.sales_breakdown(db, start, end, outlet_id), type_sort, outlet_sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
