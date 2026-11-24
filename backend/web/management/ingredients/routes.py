"""HTTP surface of the ingredients; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache, uploads
from app.core.auth import readable_outlet_id, require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.http import public_base_url
from app.models.user import User
from web.management.ingredients import repository, service
from web.management.ingredients.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MAX_SEARCH_LENGTH, PERMISSION_MANAGE, PERMISSION_VIEW
from web.management.ingredients.domain import IngredientDraft
from web.management.ingredients.schemas import (
    CatalogEntryOut,
    CatalogLinkIn,
    ImpactOut,
    IngredientEverywhereOut,
    IngredientCreateIn,
    IngredientOptionsOut,
    IngredientOut,
    IngredientPageOut,
    IngredientUpdateIn,
    OptionOut,
)
from web.management.ingredients.upload import RULE

router = APIRouter(prefix="/ingredients", tags=["web-ingredients"])

PAGE = TypeAdapter(IngredientPageOut)
OPTIONS = TypeAdapter(IngredientOptionsOut)
CATALOG = TypeAdapter(list[CatalogEntryOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _one(db: Session, row) -> IngredientOut:
    return service.describe(db, [row], public_base_url())[0]


@router.get("", response_model=IngredientPageOut)
def list_ingredients(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the name or the category"),
    id: str | None = Query(None, description="Exactly this ingredient, for a direct link to change or remove it"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    term = (search or "").strip() or None
    base_url = public_base_url()

    def build() -> IngredientPageOut:
        rows, total = repository.page_of(db, outlet_id, term, id, sort, page, size)
        return IngredientPageOut(
            items=service.describe(db, rows, base_url),
            total=total,
            page=page,
            size=size,
            unlinked=repository.unlinked_count(db, outlet_id),
        )

    with _domain_errors():
        # Free text has no end of values, so it is never a key.
        if term:
            return build()
        return cache.read("web.ingredients", (outlet_id, id, sort, page, size, base_url), build, PAGE, cache.LIST_SECONDS)


@router.get("/options", response_model=IngredientOptionsOut)
def options(db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_VIEW))):
    return cache.read(
        "web.ingredients.options",
        (),
        lambda: IngredientOptionsOut(
            categories=[OptionOut(id=item.id, name=item.name) for item in repository.categories(db)],
            units=[OptionOut(id=item.id, name=item.name) for item in repository.units(db)],
        ),
        OPTIONS,
        cache.REFERENCE_SECONDS,
    )


@router.post("", response_model=IngredientOut, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    body: IngredientCreateIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = service.create(db, outlet_id, IngredientDraft(**body.model_dump()))
    return _one(db, row)


@router.patch("/{ingredient_id}", response_model=IngredientOut)
def update_ingredient(
    ingredient_id: str,
    body: IngredientUpdateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = service.update(db, admin, ingredient_id, body.model_dump(exclude_unset=True))
    return _one(db, row)


@router.get("/{ingredient_id}/impact", response_model=ImpactOut)
def removal_impact(ingredient_id: str, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        recipes, movements = service.impact(db, admin, ingredient_id)
    return ImpactOut(recipes=recipes, movements=movements)


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(ingredient_id: str, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        service.delete(db, admin, ingredient_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{ingredient_id}/photo", response_model=IngredientOut)
async def replace_photo(
    ingredient_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        row = service.set_photo(db, admin, ingredient_id, image, RULE)
    return _one(db, row)


@router.delete("/{ingredient_id}/photo", response_model=IngredientOut)
def remove_photo(ingredient_id: str, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        row = service.remove_photo(db, admin, ingredient_id)
    return _one(db, row)


@router.post("/all-branches", response_model=IngredientEverywhereOut, status_code=status.HTTP_201_CREATED)
def create_everywhere(
    body: IngredientCreateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        created, skipped = service.create_everywhere(db, admin, IngredientDraft(**body.model_dump()))
    return IngredientEverywhereOut(created=service.describe(db, created, public_base_url()), skipped=skipped)


@router.get("/catalog", response_model=list[CatalogEntryOut])
def catalog_entries(db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_VIEW))):
    return cache.read(
        "web.ingredients.catalog",
        (),
        lambda: [CatalogEntryOut(id=entry.id, name=entry.name, unit=unit, branch_count=count) for entry, unit, count in service.catalog_entries(db)],
        CATALOG,
        cache.REFERENCE_SECONDS,
    )


@router.get("/{ingredient_id}", response_model=IngredientOut)
def get_ingredient(
    ingredient_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    # A page opened by its address is not limited to the branch picked in the filter; only a branch-bound account is.
    with _domain_errors():
        row = service.get(db, user.locked_outlet_id, ingredient_id)
    return _one(db, row)


@router.delete("/catalog/{catalog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_entry(catalog_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        service.delete_catalog_entry(db, catalog_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{ingredient_id}/catalog", response_model=IngredientOut)
def link_to_catalog(
    ingredient_id: str,
    body: CatalogLinkIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = service.link_to_catalog(db, admin, ingredient_id, body.catalog_id, body.create_new)
    return _one(db, row)


bulk.add_bulk_routes(
    router,
    PERMISSION_MANAGE,
    create_schema=IngredientCreateIn,
    create=lambda db, body, user, outlet_id: service.create(db, outlet_id, IngredientDraft(**body.model_dump())),
    create_context=writable_outlet_id,
    update_schema=IngredientUpdateIn,
    update=lambda db, ingredient_id, body, user: service.update(db, user, ingredient_id, body.model_dump(exclude_unset=True)),
    delete=lambda db, ingredient_id, user: service.delete(db, user, ingredient_id),
)
