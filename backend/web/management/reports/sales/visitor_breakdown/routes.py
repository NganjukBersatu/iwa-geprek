"""HTTP surface of the visitor breakdown, rebuilt from the legacy /pengunjung/analisa route."""
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
from web.management.reports.sales.visitor_breakdown import service
from web.management.reports.sales.visitor_breakdown.mappers import visitor_breakdown_out
from web.management.reports.sales.visitor_breakdown.schemas import VisitorBreakdownOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/visitors", tags=["v2-reports"])

SHAPE = TypeAdapter(VisitorBreakdownOut)


@router.get("", response_model=VisitorBreakdownOut)
def visitor_breakdown(
    start: Day | None = Query(None, description="Both empty means the month so far"),
    end: Day | None = Query(None),
    sort: Sort = None,
    gender_sort: Sort = None,
    category_sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.VISITORS)),
):
    """Transactions and revenue per visitor category and gender, plus the trend per day."""
    try:
        return cache.read(
            "web.reports.visitors",
            (start, end, outlet_id, sort, gender_sort, category_sort),
            lambda: visitor_breakdown_out(service.visitor_breakdown(db, start, end, outlet_id), sort, gender_sort, category_sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
