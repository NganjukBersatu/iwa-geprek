"""HTTP surface of the menu category screen; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import require_permission
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.core.sorting import Sort
from app.models.user import User
from web.management.menu.routes import PERMISSION_MANAGE
from web.management.menu_categories import service
from web.management.menu_categories.mappers import SORTING, category_out
from web.management.menu_categories.schemas import MenuCategoryCreateIn, MenuCategoryRecordOut, MenuCategoryUpdateIn

router = APIRouter(prefix="/menu-categories", tags=["web-menu-categories"])

CATEGORIES = TypeAdapter(list[MenuCategoryRecordOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise refusal(error) from error


@router.get("", response_model=list[MenuCategoryRecordOut])
def list_menu_categories(sort: Sort = None, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    def build() -> list[MenuCategoryRecordOut]:
        return SORTING.apply([category_out(row) for row in service.list_categories(db)], sort)

    return cache.read("web.menu-categories", (sort,), build, CATEGORIES, cache.REFERENCE_SECONDS)


@router.post("", response_model=MenuCategoryRecordOut, status_code=status.HTTP_201_CREATED)
def create_menu_category(body: MenuCategoryCreateIn, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        return category_out(service.create(db, body.name))


@router.patch("/{category_id}", response_model=MenuCategoryRecordOut)
def update_menu_category(category_id: str, body: MenuCategoryUpdateIn, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        return category_out(service.update(db, category_id, body.name))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_category(category_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        service.delete(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
