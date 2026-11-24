"""HTTP surface of the margin report."""
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
from web.management.reports.transactions.margin import service
from web.management.reports.transactions.margin.mappers import margin_out
from web.management.reports.transactions.margin.schemas import MarginOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/margin", tags=["v2-reports"])

SHAPE = TypeAdapter(MarginOut)


@router.get("", response_model=MarginOut)
def margin(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.MARGIN)),
):
    """Revenue, cost, and margin per menu; voided orders are left out."""
    try:
        return cache.read(
            "web.reports.margin",
            (start, end, outlet_id, sort),
            lambda: margin_out(service.margin(db, start, end, outlet_id), sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
