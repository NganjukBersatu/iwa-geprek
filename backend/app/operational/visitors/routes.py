"""Visitor kinds and genders of the tablet's branch; every rule lives in app.core.visitors."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import visitors
from app.core.auth import current_user, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.device import Device
from app.models.order import Order
from app.models.user import User
from app.models.visitor import VisitorCategory, VisitorGender
from app.operational.device import tablet

router = APIRouter(prefix="/visitors", tags=["v2-operational-visitors"])

MAX_NAME_LENGTH = 40


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    asks_gender: bool = False
    is_active: bool = True


class GenderIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    is_active: bool = True


class VisitorCategoryOut(BaseModel):
    id: str
    name: str
    asks_gender: bool
    is_active: bool
    # Orders that carry it, so the screen can say so before a delete.
    used_by: int


class GenderOut(BaseModel):
    id: str
    name: str
    is_active: bool
    used_by: int


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _category_out(row: VisitorCategory, used: dict[str, int]) -> VisitorCategoryOut:
    return VisitorCategoryOut(id=row.id, name=row.name, asks_gender=row.asks_gender, is_active=row.is_active, used_by=used.get(row.id, 0))


def _gender_out(row: VisitorGender, used: dict[str, int]) -> GenderOut:
    return GenderOut(id=row.id, name=row.name, is_active=row.is_active, used_by=used.get(row.id, 0))


@router.get("/categories", response_model=list[VisitorCategoryOut])
def list_categories(device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Switched-off ones included, for the settings screen; the cashier list shows only the active ones."""
    used = visitors.usage(db, Order.visitor_category_id, device.outlet_id)
    return [_category_out(row, used) for row in visitors.categories_of(db, device.outlet_id)]


@router.post("/categories", response_model=VisitorCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryIn, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(visitors.PERMISSION_MANAGE))):
    with _domain_errors():
        row = visitors.create_category(db, device.outlet_id, body.name, body.asks_gender, body.is_active)
    return _category_out(row, {})


@router.put("/categories/{category_id}", response_model=VisitorCategoryOut)
def update_category(
    category_id: str,
    body: CategoryIn,
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(visitors.PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = visitors.update_category(db, device.outlet_id, category_id, body.name, body.asks_gender, body.is_active)
    return _category_out(row, visitors.usage(db, Order.visitor_category_id, device.outlet_id))


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(visitors.PERMISSION_MANAGE))):
    with _domain_errors():
        visitors.delete_category(db, device.outlet_id, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/genders", response_model=list[GenderOut])
def list_genders(device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(current_user)):
    used = visitors.usage(db, Order.visitor_gender_id, device.outlet_id)
    return [_gender_out(row, used) for row in visitors.genders_of(db, device.outlet_id)]


@router.post("/genders", response_model=GenderOut, status_code=status.HTTP_201_CREATED)
def create_gender(body: GenderIn, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(visitors.PERMISSION_MANAGE))):
    with _domain_errors():
        row = visitors.create_gender(db, device.outlet_id, body.name, body.is_active)
    return _gender_out(row, {})


@router.put("/genders/{gender_id}", response_model=GenderOut)
def update_gender(
    gender_id: str,
    body: GenderIn,
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(visitors.PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = visitors.update_gender(db, device.outlet_id, gender_id, body.name, body.is_active)
    return _gender_out(row, visitors.usage(db, Order.visitor_gender_id, device.outlet_id))


@router.delete("/genders/{gender_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gender(gender_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(visitors.PERMISSION_MANAGE))):
    with _domain_errors():
        visitors.delete_gender(db, device.outlet_id, gender_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
