"""HTTP surface of the menu screen; every rule lives in app.core.catalog.menu."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache, uploads
from app.core.auth import require_permission
from app.core.catalog import availability
from app.core.catalog import menu as catalog_menu
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.core.uploads import KIND_PHOTO, UploadRule
from app.models.user import User
from web.management.menu import repository, service
from web.management.menu.mappers import category_out, menu_out
from web.management.menu.schemas import MenuCategoryOut, MenuCreateIn, MenuItemOut, MenuItemPageOut, MenuUpdateIn
from app.core.sorting import Sort

router = APIRouter(prefix="/menu", tags=["web-menu"])

PERMISSION_MANAGE = "menu.kelola"
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100

MENU_PAGE = TypeAdapter(MenuItemPageOut)
MENU_ITEM = TypeAdapter(MenuItemOut)
CATEGORIES = TypeAdapter(list[MenuCategoryOut])

PHOTO_RULE = UploadRule(kinds=frozenset({KIND_PHOTO}), unreadable_note="Pilih foto lain.", not_saved="Foto menu gagal disimpan. Coba lagi.")


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _out(db: Session, menu_id: str, base_url: str) -> MenuItemOut:
    found = repository.with_category(db, menu_id)
    if found is None:
        raise DomainError(catalog_menu.MENU_NOT_FOUND, status=catalog_menu.NOT_FOUND)
    item, category_name = found
    return menu_out(item, category_name, catalog_menu.branch_prices(db, [item.id]).get(item.id, {}), availability.outlets_off(db, [item.id]).get(item.id, []), base_url)


@router.get("", response_model=MenuItemPageOut)
def list_menu(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the menu or category name"),
    category_id: str | None = Query(None),
    available: bool | None = Query(None),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    term = (search or "").strip() or None
    base_url = public_base_url()

    def build() -> MenuItemPageOut:
        rows, total = repository.page_of(db, term, category_id, available, sort, page, size)
        prices = catalog_menu.branch_prices(db, [item.id for item, _ in rows])
        unavailable = availability.outlets_off(db, [item.id for item, _ in rows])
        return MenuItemPageOut(
            items=[menu_out(item, name, prices.get(item.id, {}), unavailable.get(item.id, []), base_url) for item, name in rows], total=total, page=page, size=size
        )

    if term:
        return build()
    return cache.read("web.menu", (category_id, available, sort, page, size, base_url), build, MENU_PAGE, cache.REFERENCE_SECONDS)


@router.get("/categories", response_model=list[MenuCategoryOut])
def list_categories(db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    return cache.read(
        "web.menu.categories", (), lambda: [category_out(category) for category in repository.menu_categories(db)], CATEGORIES, cache.REFERENCE_SECONDS
    )


@router.get("/{menu_id}", response_model=MenuItemOut)
def menu_detail(menu_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    base_url = public_base_url()
    with _domain_errors():
        return cache.read("web.menu.detail", (menu_id, base_url), lambda: _out(db, menu_id, base_url), MENU_ITEM, cache.REFERENCE_SECONDS)


@router.post("", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
def create_menu(
    body: MenuCreateIn, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))
):
    with _domain_errors():
        item = service.create(db, body)
        return _out(db, item.id, public_base_url())


@router.patch("/{menu_id}", response_model=MenuItemOut)
def update_menu(
    menu_id: str,
    body: MenuUpdateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.update(db, menu_id, {field: getattr(body, field) for field in body.model_fields_set})
        return _out(db, menu_id, public_base_url())


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(menu_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        catalog_menu.delete(db, menu_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{menu_id}/photo", response_model=MenuItemOut)
async def replace_photo(
    menu_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        image = await uploads.receive(file, PHOTO_RULE)
        catalog_menu.set_photo(db, menu_id, image, PHOTO_RULE)
        return _out(db, menu_id, public_base_url())


bulk.add_bulk_routes(
    router,
    PERMISSION_MANAGE,
    create_schema=MenuCreateIn,
    create=lambda db, body, _user, _context: service.create(db, body),
    update_schema=MenuUpdateIn,
    update=lambda db, menu_id, body, _user: service.update(db, menu_id, {field: getattr(body, field) for field in body.model_fields_set}),
    delete=lambda db, menu_id, _user: catalog_menu.delete(db, menu_id),
)
