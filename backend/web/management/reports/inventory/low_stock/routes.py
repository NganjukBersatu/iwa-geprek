"""HTTP surface of the low stock report."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.models.user import User
from web.management.reports.inventory.low_stock import service
from web.management.reports.inventory.low_stock.mappers import low_stock_out
from web.management.reports.inventory.low_stock.schemas import LowStockOut
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])


@router.get("/low-stock", response_model=LowStockOut)
def low_stock(
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.INGREDIENT_STOCK)),
):
    """Ingredients and resold items about to run out, now."""
    return low_stock_out(service.low_stock(db, outlet_id))
