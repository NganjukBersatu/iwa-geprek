"""HTTP surface of the ingredient stock report."""
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
from web.management.reports.common import as_http, month_to_date
from web.management.reports.inventory.ingredient_stock import service
from web.management.reports.inventory.ingredient_stock.mappers import ingredient_stock_out
from web.management.reports.inventory.ingredient_stock.schemas import IngredientStockOut
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(IngredientStockOut)


@router.get("/ingredient-stock", response_model=IngredientStockOut)
def ingredient_stock(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.INGREDIENT_STOCK)),
):
    """Ingredient stock over any period; defaults to the current month."""
    try:
        start, end = month_to_date(start, end)
    except DomainError as error:
        raise as_http(error) from error
    return cache.read(
        "web.reports.ingredient-stock",
        (start, end, outlet_id, sort),
        lambda: ingredient_stock_out(service.sorted_report(service.stock_report(db, outlet_id, start, end), sort)),
        SHAPE,
        cache.REPORT_SECONDS,
    )
