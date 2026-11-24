"""HTTP surface of Master Resep; recipes are per branch: the list may cover every branch, a recipe itself always belongs to one."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate, require_permission, writable_outlet_id
from app.core.catalog import recipe_book as service
from app.core.catalog.recipe_schemas import IngredientOptionOut, RecipeOut, RecipePageOut, RecipeSaveIn, RecipeSaveOut
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.user import User
from web.management.recipes.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MAX_SEARCH_LENGTH

router = APIRouter(prefix="/recipes", tags=["web-recipes"])


PAGE = TypeAdapter(RecipePageOut)
INGREDIENTS = TypeAdapter(list[IngredientOptionOut])
RECIPE = TypeAdapter(RecipeOut)


may_read = require_gate(service.READ_GATE)


@router.get("", response_model=RecipePageOut)
def list_recipes(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the menu name or the category"),
    recipe: Literal["ada", "belum"] | None = Query(None, description="Only menus with, or still without, a recipe at this branch"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(may_read),
):
    term = (search or "").strip() or None

    def build() -> RecipePageOut:
        items, total = service.list_recipes(db, user, outlet_id, term, recipe, page, size)
        return RecipePageOut(items=items, total=total, page=page, size=size)

    if term:
        return build()
    # Costs are shown only to those allowed to see them.
    sees_cost = user.allows(service.PERMISSION_COST)
    return cache.read("web.recipes", (outlet_id, recipe, page, size, sees_cost), build, PAGE, cache.REFERENCE_SECONDS)


@router.get("/ingredients", response_model=list[IngredientOptionOut])
def ingredient_options(
    search: str | None = Query(None, max_length=service.OPTION_MAX_SEARCH, description="Part of the ingredient name"),
    page: int = Query(1, ge=1),
    size: int | None = Query(None, ge=1, le=service.OPTION_MAX_SIZE, description="Rows per page; leaving it out returns every ingredient (old clients only)"),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(may_read),
):
    term = (search or "").strip() or None

    def build() -> list[IngredientOptionOut]:
        return service.ingredient_options(db, user, outlet_id, term, page, size)

    # Free text has no end of values, so it is never a key.
    if term:
        return build()
    return cache.read("web.recipes.ingredients", (outlet_id, user.allows(service.PERMISSION_COST), page, size), build, INGREDIENTS, cache.REFERENCE_SECONDS)


@router.get("/{menu_id}", response_model=RecipeOut)
def recipe_of(menu_id: str, outlet_id: str = Depends(writable_outlet_id), db: Session = Depends(get_db), user: User = Depends(may_read)):
    try:
        return cache.read(
            "web.recipes.detail",
            (outlet_id, menu_id, user.allows(service.PERMISSION_COST)),
            lambda: service.recipe_of(db, user, outlet_id, menu_id),
            RECIPE,
            cache.REFERENCE_SECONDS,
        )
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.put("/{menu_id}", response_model=RecipeSaveOut)
def save_recipe(
    menu_id: str,
    body: RecipeSaveIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(service.PERMISSION_MANAGE)),
):
    """With all_branches and missing ingredients not yet confirmed, nothing is saved and the answer lists them."""
    try:
        return service.save(db, user, outlet_id, menu_id, body)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
