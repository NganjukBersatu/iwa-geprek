"""HTTP surface of the Varian dan Ekstra screen; every rule lives in app.core.catalog."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import bulk, cache
from app.core.auth import readable_outlet_id, require_gate, require_permission, writable_outlet_id
from app.core.catalog import options, recipe_book as recipe_service, recipes
from app.core.catalog.recipe_schemas import IngredientOptionOut
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.sorting import RowSorting, Sort
from app.models.extra import Extra
from app.models.menu_item import MenuItem
from app.models.user import User
from app.models.variant import VariantChoice
from web.management.options import service
from web.management.options.schemas import (
    ExtraCategoryOut,
    ExtraIn,
    ManagedExtraOut,
    ExtraUpdateIn,
    OptionMenuOut,
    OptionRecipeIn,
    OptionRecipeOut,
    VariantGroupIn,
    ManagedVariantGroupOut,
    VariantGroupUpdateIn,
)

router = APIRouter(tags=["web-options"])

CHOICE_NOT_FOUND = "Pilihan varian tidak ditemukan."

GROUPS = TypeAdapter(list[ManagedVariantGroupOut])
EXTRAS = TypeAdapter(list[ManagedExtraOut])
EXTRA_CATEGORIES = TypeAdapter(list[ExtraCategoryOut])
MENUS = TypeAdapter(list[OptionMenuOut])
INGREDIENTS = TypeAdapter(list[IngredientOptionOut])

# An extra sold everywhere counts as reaching more branches than any list can.
EVERY_BRANCH = 10**6

GROUP_SORTING: RowSorting[ManagedVariantGroupOut] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "choices": lambda row: ", ".join(choice.name for choice in row.choices),
        "menus": lambda row: len(row.menu_ids),
    },
    identity=lambda row: row.id,
)

EXTRA_SORTING: RowSorting[ManagedExtraOut] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "category": lambda row: row.category_name,
        "branches": lambda row: EVERY_BRANCH if row.outlet_ids is None else len(row.outlet_ids),
        "menus": lambda row: len(row.menu_ids),
        "price": lambda row: row.price,
    },
    identity=lambda row: row.id,
)


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _choices(body: VariantGroupIn | VariantGroupUpdateIn) -> list[options.ChoiceInput] | None:
    if body.choices is None:
        return None
    return [options.ChoiceInput(choice.id, choice.name, choice.color, choice.is_active) for choice in body.choices]


# --- Variant groups ---------------------------------------------------------------


@router.get("/variant-groups", response_model=list[ManagedVariantGroupOut])
def list_groups(
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
):
    return cache.read("web.variant-groups", (outlet_id, sort), lambda: GROUP_SORTING.apply(service.groups(db, outlet_id), sort), GROUPS, cache.REFERENCE_SECONDS)


@router.get("/variant-groups/{group_id}", response_model=ManagedVariantGroupOut)
def get_group(
    group_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
):
    with _domain_errors():
        group = options.get_group(db, group_id)
    return service.groups(db, outlet_id, [group])[0]


@router.post("/variant-groups", response_model=ManagedVariantGroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    body: VariantGroupIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
):
    with _domain_errors():
        group = options.create_group(db, body.name, body.required, body.is_active, _choices(body), body.menu_ids, body.outlet_id)
    return service.groups(db, outlet_id, [group])[0]


@router.patch("/variant-groups/{group_id}", response_model=ManagedVariantGroupOut)
def update_group(
    group_id: str,
    body: VariantGroupUpdateIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
):
    changes = {field: getattr(body, field) for field in body.model_fields_set}
    if "choices" in changes:
        changes["choices"] = _choices(body)
    with _domain_errors():
        group = options.update_group(db, group_id, changes)
    return service.groups(db, outlet_id, [group])[0]


@router.delete("/variant-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(options.PERMISSION_VARIANTS))):
    with _domain_errors():
        options.delete_group(db, group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/variant-groups/choices/{choice_id}/recipe", response_model=OptionRecipeOut)
def save_choice_recipe(
    choice_id: str,
    body: OptionRecipeIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
):
    if db.get(VariantChoice, choice_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CHOICE_NOT_FOUND)
    with _domain_errors():
        return service.save_recipe(db, user, recipes.KIND_VARIANT, choice_id, outlet_id, body)


# --- Extras ----------------------------------------------------------------------------


@router.get("/extras", response_model=list[ManagedExtraOut])
def list_extras(
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
):
    return cache.read("web.extras", (outlet_id, sort), lambda: EXTRA_SORTING.apply(service.extras(db, outlet_id), sort), EXTRAS, cache.REFERENCE_SECONDS)


@router.get("/extras/categories", response_model=list[ExtraCategoryOut])
def extra_categories(db: Session = Depends(get_db), _: User = Depends(require_permission(options.PERMISSION_EXTRAS))):
    return cache.read("web.extras.categories", (), lambda: service.extra_categories(db), EXTRA_CATEGORIES, cache.REFERENCE_SECONDS)


@router.get("/extras/{extra_id}", response_model=ManagedExtraOut)
def get_extra(
    extra_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
):
    with _domain_errors():
        extra = options.get_extra(db, extra_id)
    return service.extras(db, outlet_id, [extra])[0]


@router.post("/extras", response_model=ManagedExtraOut, status_code=status.HTTP_201_CREATED)
def create_extra(
    body: ExtraIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
):
    with _domain_errors():
        extra = options.create_extra(db, body.name, body.price, body.is_active, body.outlet_ids, body.branch_prices, body.category_id, body.menu_ids)
    return service.extras(db, outlet_id, [extra])[0]


@router.patch("/extras/{extra_id}", response_model=ManagedExtraOut)
def update_extra(
    extra_id: str,
    body: ExtraUpdateIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
):
    with _domain_errors():
        extra = options.update_extra(db, extra_id, {field: getattr(body, field) for field in body.model_fields_set})
    return service.extras(db, outlet_id, [extra])[0]


@router.delete("/extras/{extra_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_extra(extra_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(options.PERMISSION_EXTRAS))):
    with _domain_errors():
        options.delete_extra(db, extra_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/extras/{extra_id}/recipe", response_model=OptionRecipeOut)
def save_extra_recipe(
    extra_id: str,
    body: OptionRecipeIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
):
    if db.get(Extra, extra_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=options.EXTRA_NOT_FOUND)
    with _domain_errors():
        return service.save_recipe(db, user, recipes.KIND_EXTRA, extra_id, outlet_id, body)


may_manage_options = require_gate(options.MANAGE_GATE)


@router.get("/option-menus", response_model=list[OptionMenuOut])
def option_menus(db: Session = Depends(get_db), _: User = Depends(may_manage_options)):
    """Every menu by name, to choose which ones a group or an extra goes on."""
    return cache.read(
        "web.option-menus",
        (),
        lambda: [OptionMenuOut(id=menu_id, name=name) for menu_id, name in db.execute(select(MenuItem.id, MenuItem.name).order_by(MenuItem.name)).all()],
        MENUS,
        cache.REFERENCE_SECONDS,
    )


@router.get("/option-ingredients", response_model=list[IngredientOptionOut])
def option_ingredients(
    search: str | None = Query(None, max_length=recipe_service.OPTION_MAX_SEARCH, description="Part of the ingredient name"),
    page: int = Query(1, ge=1),
    size: int | None = Query(None, ge=1, le=recipe_service.OPTION_MAX_SIZE, description="Rows per page; leaving it out returns every ingredient (old clients only)"),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(may_manage_options),
):
    term = (search or "").strip() or None

    def build() -> list[IngredientOptionOut]:
        return recipe_service.ingredient_options(db, user, outlet_id, term, page, size)

    # What it shows depends on whether the viewer may see costs; free text has no end of values, so it is never a key.
    if term:
        return build()
    return cache.read("web.option-ingredients", (outlet_id, user.allows(recipe_service.PERMISSION_COST), page, size), build, INGREDIENTS, cache.REFERENCE_SECONDS)


groups_bulk = APIRouter(prefix="/variant-groups")
extras_bulk = APIRouter(prefix="/extras")
bulk.add_bulk_routes(groups_bulk, options.PERMISSION_VARIANTS, delete=lambda db, group_id, _user: options.delete_group(db, group_id))
bulk.add_bulk_routes(extras_bulk, options.PERMISSION_EXTRAS, delete=lambda db, extra_id, _user: options.delete_extra(db, extra_id))
router.include_router(groups_bulk)
router.include_router(extras_bulk)
