"""Master Resep of the tablet's branch; reading and saving live in app.core.catalog.recipe_book."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import require_gate, require_permission
from app.core.catalog import recipe_book
from app.core.catalog.recipe_schemas import IngredientOptionOut, RecipeLineIn, RecipeOut, RecipePageOut, RecipeSaveIn
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.device import Device
from app.models.user import User
from app.operational.device import tablet

router = APIRouter(prefix="/recipes", tags=["v2-operational-recipes"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100


class TabletRecipeIn(BaseModel):
    """Only the ingredients; costing settings and spreading to other branches stay on the web."""

    lines: list[RecipeLineIn] = Field(max_length=100)


may_read = require_gate(recipe_book.READ_GATE)


@router.get("", response_model=RecipePageOut)
def list_recipes(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH),
    recipe: Literal["ada", "belum"] | None = Query(None, description="Only menus with, or still without, a recipe at this branch"),
    sort: str | None = Query(None, pattern="^-?name$", description="name, or -name for descending; no choice means by category, then name"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    user: User = Depends(may_read),
):
    items, total = recipe_book.list_recipes(db, user, device.outlet_id, (search or "").strip() or None, recipe, page, size, sort)
    return RecipePageOut(items=items, total=total, page=page, size=size)


@router.get("/ingredients", response_model=list[IngredientOptionOut])
def ingredients(
    search: str | None = Query(None, max_length=recipe_book.OPTION_MAX_SEARCH, description="Part of the ingredient name"),
    page: int = Query(1, ge=1),
    size: int | None = Query(None, ge=1, le=recipe_book.OPTION_MAX_SIZE, description="Rows per page; leaving it out returns every ingredient (old clients only)"),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    user: User = Depends(may_read),
):
    return recipe_book.ingredient_options(db, user, device.outlet_id, (search or "").strip() or None, page, size)


@router.get("/{menu_id}", response_model=RecipeOut)
def read_recipe(menu_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(may_read)):
    """Satu resep di cabang tablet, untuk lembar Resep yang dibuka dari daftar "Dipakai di menu"; tidak di-cache karena resep bisa diubah kapan saja."""
    try:
        return recipe_book.recipe_of(db, user, device.outlet_id, menu_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.put("/{menu_id}", response_model=RecipeOut)
def save_recipe(
    menu_id: str,
    body: TabletRecipeIn,
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(recipe_book.PERMISSION_MANAGE)),
):
    """Replaces the recipe at the tablet's branch; an empty list removes it."""
    try:
        saved = recipe_book.save(db, user, device.outlet_id, menu_id, RecipeSaveIn(lines=body.lines))
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return saved.recipe
