"""HTTP surface of the promo usage report."""
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
from web.management.reports.transactions.promos import service
from web.management.reports.transactions.promos.mappers import promos_out
from web.management.reports.transactions.promos.schemas import PromosOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/promos", tags=["v2-reports"])

SHAPE = TypeAdapter(PromosOut)


@router.get("", response_model=PromosOut)
def promos(
    start: Day | None = Query(None, description="Defaults to the first of this month"),
    end: Day | None = Query(None, description="Defaults to today"),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.PROMOS)),
):
    """How many orders used each promo and how much it took off."""
    try:
        return cache.read(
            "web.reports.promos",
            (start, end, outlet_id, sort),
            lambda: promos_out(service.promos(db, start, end, outlet_id), sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
