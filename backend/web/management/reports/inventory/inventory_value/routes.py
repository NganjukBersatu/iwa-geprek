"""HTTP surface of the inventory value."""
from fastapi import APIRouter, Depends
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.models.user import User
from web.management.reports.inventory.inventory_value import service
from web.management.reports.inventory.inventory_value.mappers import inventory_value_out
from web.management.reports.inventory.inventory_value.schemas import InventoryValueOut
from web.management.reports import gates

router = APIRouter(prefix="/reports", tags=["v2-reports"])

SHAPE = TypeAdapter(InventoryValueOut)


@router.get("/inventory-value", response_model=InventoryValueOut)
def inventory_value(
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.INVENTORY_VALUE)),
):
    """Money sitting on the shelf now, not per period."""
    return cache.read(
        "web.reports.inventory-value",
        (outlet_id,),
        lambda: inventory_value_out(service.inventory_value(db, outlet_id)),
        SHAPE,
        cache.REPORT_SECONDS,
    )
