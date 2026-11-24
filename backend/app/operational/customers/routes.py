"""Customer suggestions on the till; every rule lives in app.core.customers."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import customers
from app.core.auth import require_permission
from app.core.database import get_db
from app.models.device import Device
from app.models.user import User
from app.operational.device import cashier_tablet

router = APIRouter(prefix="/customers", tags=["v2-operational-customers"])


class CustomerSuggestionOut(BaseModel):
    id: str
    name: str
    contact: str | None
    visit_count: int


@router.get("/suggestions", response_model=list[CustomerSuggestionOut])
def suggestions(
    q: str = Query("", max_length=100),
    _device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(customers.PERMISSION_VIEW)),
):
    """A name or a phone number, either in part; never cached, since each keystroke asks something new."""
    return [CustomerSuggestionOut(id=row.id, name=row.name, contact=row.contact, visit_count=row.visit_count) for row in customers.suggest(db, q)]
