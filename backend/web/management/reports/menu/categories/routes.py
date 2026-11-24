"""HTTP surface of the categories report."""
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
from web.management.reports import gates
from web.management.reports.menu.categories import service
from web.management.reports.menu.categories.mappers import categories_out
from web.management.reports.menu.categories.schemas import CategoriesOut

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(CategoriesOut)


@router.get("/categories", response_model=CategoriesOut)
def category_sales(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    sort: Sort = None,
    unsold_sort: Sort = None,
    menu_sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.CATEGORIES)),
):
    """Sales and profit per menu category against the period before, per menu, and the menu items that did not sell."""
    try:
        return cache.read(
            "web.reports.categories",
            (start, end, outlet_id, sort, unsold_sort, menu_sort),
            lambda: categories_out(service.categories(db, start, end, outlet_id), sort, unsold_sort, menu_sort),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
