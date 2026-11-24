"""HTTP surface of the voids report."""
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
from web.management.reports.menu.voids import service
from web.management.reports.menu.voids.constants import VOIDS_PER_PAGE_DEFAULT, VOIDS_PER_PAGE_MAX
from web.management.reports.menu.voids.mappers import voids_out
from web.management.reports.menu.voids.schemas import VoidsOut
from app.core.sorting import Sort
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(VoidsOut)


@router.get("/voids", response_model=VoidsOut)
def voided_orders(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(VOIDS_PER_PAGE_DEFAULT, ge=1, le=VOIDS_PER_PAGE_MAX),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.VOIDS)),
):
    """Voided orders of the business days in the range, the days their sale belongs to."""
    try:
        return cache.read(
            "web.reports.voids",
            (start, end, sort, page, per_page, outlet_id),
            lambda: voids_out(service.voids(db, start, end, sort, page, per_page, outlet_id)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
