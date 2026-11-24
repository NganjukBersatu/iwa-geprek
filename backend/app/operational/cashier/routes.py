"""What the till reads; the branch is the paired tablet's."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import visitors
from app.core.auth import require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.finance import session_control
from app.core.finance.payment_methods import missing_requirements
from app.core.http import public_base_url, static_url
from app.core.orders.create import PERMISSION
from app.models.device import Device
from app.models.user import User
from app.operational.cashier import service
from app.operational.cashier.schemas import CashierMenuOut, CashierMethodOut, CashierPromoOut, ShopOut, StationOut, VisitorChoicesOut, VisitorGenderOut, VisitorKindOut
from app.operational.device import cashier_tablet

router = APIRouter(prefix="/cashier", tags=["v2-operational-cashier"])

DEFAULT_BEST_SELLERS = 10
MAX_BEST_SELLERS = 50


@router.get("/menu", response_model=list[CashierMenuOut])
def menu(device: Device = Depends(cashier_tablet), db: Session = Depends(get_db), _user: User = Depends(require_permission(PERMISSION))):
    return service.menu(db, device.outlet_id, public_base_url())


@router.get("/best-sellers", response_model=list[str])
def best_sellers(
    limit: int = Query(DEFAULT_BEST_SELLERS, ge=1, le=MAX_BEST_SELLERS),
    _device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(PERMISSION)),
):
    """Menu ids only; the till takes everything else from the menu."""
    return service.best_seller_ids(db, limit)


@router.get("/payment-methods", response_model=list[CashierMethodOut])
def payment_methods(
    with_unready: bool = Query(False),
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(PERMISSION)),
):
    """`with_unready` adds the switched-on methods that are not yet set up; older tills leave it off and only ever see usable ones."""
    try:
        found = service.methods(db, device.outlet_id, with_unready)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return [
        CashierMethodOut(
            code=method.code,
            label=method.label,
            needs_change=method.needs_change,
            icon=method.icon,
            missing=missing_requirements(method),
            image_url=static_url(public_base_url(), method.image_path),
            note=method.note or "",
        )
        for method in found
    ]


@router.get("/promos", response_model=list[CashierPromoOut])
def promos(device: Device = Depends(cashier_tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION))):
    """Switched on and not yet ended, so a till that goes offline overnight still knows tomorrow's promos."""
    return [
        CashierPromoOut(
            id=row.id,
            name=row.name,
            kind=row.kind,
            discount_type=row.discount_type,
            value=row.value,
            product_ids=list(row.product_ids or []),
            minimum_spend=row.minimum_spend,
            activation=row.activation,
            starts_on=row.starts_on,
            ends_on=row.ends_on,
        )
        for row in service.promos(db, session_control.business_day_of(db, user.id), device.outlet_id)
    ]


@router.get("/shop", response_model=ShopOut)
def shop(device: Device = Depends(cashier_tablet), db: Session = Depends(get_db), _user: User = Depends(require_permission(PERMISSION))):
    return service.shop(db, device.outlet_id)


@router.get("/stations", response_model=list[StationOut])
def stations(_device: Device = Depends(cashier_tablet), db: Session = Depends(get_db), _user: User = Depends(require_permission(PERMISSION))):
    return service.stations(db)


@router.get("/visitors", response_model=VisitorChoicesOut)
def visitor_choices(device: Device = Depends(cashier_tablet), db: Session = Depends(get_db), _user: User = Depends(require_permission(PERMISSION))):
    return VisitorChoicesOut(
        categories=[VisitorKindOut(id=row.id, name=row.name, asks_gender=row.asks_gender) for row in visitors.categories_of(db, device.outlet_id) if row.is_active],
        genders=[VisitorGenderOut(id=row.id, name=row.name) for row in visitors.genders_of(db, device.outlet_id) if row.is_active],
    )
