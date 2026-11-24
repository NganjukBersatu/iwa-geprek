"""HTTP surface of the variants report."""
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
from web.management.reports.menu.variants import service
from web.management.reports.menu.variants.mappers import variants_out
from web.management.reports.menu.variants.schemas import VariantsOut
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(VariantsOut)


@router.get("/variants", response_model=VariantsOut)
def variant_sales(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    by_menu: bool = Query(False, description="Split further per menu, such as Latte Ice vs Latte Hot"),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.OPTIONS)),
):
    """Which variant choices sell most."""
    try:
        return cache.read(
            "web.reports.variants",
            (start, end, by_menu, outlet_id, sort),
            lambda: variants_out(service.variants(db, start, end, by_menu, outlet_id), sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
