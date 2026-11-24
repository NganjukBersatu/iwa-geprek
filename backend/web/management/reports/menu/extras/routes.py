"""HTTP surface of the extras report."""
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
from web.management.reports.menu.extras import service
from web.management.reports.menu.extras.mappers import extras_out
from web.management.reports.menu.extras.schemas import ExtrasOut
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(ExtrasOut)


@router.get("/extras", response_model=ExtrasOut)
def extra_sales(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.OPTIONS)),
):
    """Which extras sell most and earn most."""
    try:
        return cache.read(
            "web.reports.extras",
            (start, end, outlet_id, sort),
            lambda: extras_out(service.extras(db, start, end, outlet_id), sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
