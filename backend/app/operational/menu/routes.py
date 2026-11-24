from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache, uploads
from app.core.auth import current_user, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.models.user import User
from app.operational.menu import repository, service
from app.operational.menu.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_SEARCH_LENGTH,
    PERMISSION_AVAILABILITY,
    PERMISSION_MANAGE,
)
from app.models.device import Device
from app.operational.device import tablet, tablet_outlet_id
from app.operational.menu.mappers import category_out, menu_detail_out, menu_out, menu_page_out
from app.operational.menu.schemas import AvailabilityIn, CategoryOut, MenuChangesIn, MenuDetailOut, MenuOut, MenuPageOut
from app.operational.menu.upload import RULE

router = APIRouter(prefix="/menu", tags=["v2-operational-menu"])

MENU_PAGE = TypeAdapter(MenuPageOut)
CATEGORIES = TypeAdapter(list[CategoryOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("", response_model=MenuPageOut)
def list_menu(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the menu or category name"),
    category_id: str | None = Query(None),
    sort: str | None = Query(None, pattern="^-?(name|time)$", description="name or time, a leading minus for descending; no choice means by category, then name"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _user: User = Depends(current_user),
    outlet_id: str = Depends(tablet_outlet_id),
):
    base_url = public_base_url()

    def build() -> MenuPageOut:
        return menu_page_out(service.page_of(db, outlet_id, search, category_id, page, size, sort), base_url)

    if (search or "").strip():
        return build()
    return cache.read("operational.menu", (outlet_id, category_id, sort, page, size, base_url), build, MENU_PAGE, cache.REFERENCE_SECONDS)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), _user: User = Depends(current_user)):
    return cache.read(
        "operational.menu.categories", (), lambda: [category_out(category) for category in repository.menu_categories(db)], CATEGORIES, cache.REFERENCE_SECONDS
    )


# Tidak di-cache: stok bahan dan jumlah terjual berubah di setiap penjualan, dan tablet memuat ulang lewat sinyal /live.
@router.get("/{menu_id}", response_model=MenuDetailOut)
def menu_detail(
    menu_id: str,
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        detail = service.detail(db, user, device.outlet_id, menu_id)
    return menu_detail_out(detail, public_base_url())


@router.patch("/{menu_id}", response_model=MenuOut)
def update_menu(
    menu_id: str,
    body: MenuChangesIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    changes = {field: getattr(body, field) for field in body.model_fields_set}
    with _domain_errors():
        view = service.update(db, outlet_id, menu_id, changes)
    return menu_out(view, public_base_url())


@router.patch("/{menu_id}/availability", response_model=MenuOut)
def set_availability(
    menu_id: str,
    body: AvailabilityIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_AVAILABILITY)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        view = service.set_available(db, user, outlet_id, menu_id, body.is_available)
    return menu_out(view, public_base_url())


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, menu_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{menu_id}/photo", response_model=MenuOut)
async def replace_photo(
    menu_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        view = service.set_photo(db, outlet_id, menu_id, image)
    return menu_out(view, public_base_url())
