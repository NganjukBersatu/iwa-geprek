"""Reads and plain writes of ingredients; no rule lives here."""
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.core.sorting import SqlSorting
from app.core.stock_balances import last_move_of
from app.models.category import Category, Unit
from app.models.extra import ExtraRecipe
from app.models.ingredient import CatalogIngredient, Ingredient, IngredientCard, RecipeIngredient
from app.models.outlet import Outlet
from app.models.variant import VariantChoiceRecipe
from web.management.ingredients.constants import CATEGORY_KIND


SORTING = SqlSorting(
    columns={
        "name": Ingredient.name,
        "category": Category.name,
        "balance": Ingredient.balance,
        "unit_price": Ingredient.unit_price,
        "active": Ingredient.is_active,
    },
    default=(Category.name, Ingredient.name),
    tiebreak=Ingredient.id,
)


def page_of(
    db: Session, outlet_id: str | None, search: str | None, ingredient_id: str | None, sort: str | None, page: int, size: int
) -> tuple[list[Ingredient], int]:
    filters = []
    if outlet_id:
        filters.append(Ingredient.outlet_id == outlet_id)
    if ingredient_id:
        filters.append(Ingredient.id == ingredient_id)
    if search:
        filters.append(or_(contains(Ingredient.name, search), contains(Category.name, search)))
    joined = lambda statement: statement.outerjoin(Category, Category.id == Ingredient.category_id)  # noqa: E731
    total = db.scalar(joined(select(func.count(Ingredient.id)).select_from(Ingredient)).where(*filters)) or 0
    rows = db.scalars(joined(select(Ingredient)).where(*filters).order_by(*SORTING.order_by(sort)).offset((page - 1) * size).limit(size))
    return list(rows), total


def unlinked_count(db: Session, outlet_id: str | None) -> int:
    query = select(func.count(Ingredient.id)).where(Ingredient.catalog_id.is_(None))
    if outlet_id:
        query = query.where(Ingredient.outlet_id == outlet_id)
    return db.scalar(query) or 0


def balances(db: Session, ingredient_ids: list[str]) -> dict[str, Decimal]:
    rows = db.execute(select(Ingredient.id, Ingredient.balance).where(Ingredient.id.in_(ingredient_ids)))
    return {ingredient_id: Decimal(str(balance)) for ingredient_id, balance in rows}


def last_moves(db: Session, ingredient_ids: list[str]) -> dict[str, date]:
    """One index lookup per ingredient, however long its history."""
    rows = db.execute(select(Ingredient.id, last_move_of(Ingredient.id)).where(Ingredient.id.in_(ingredient_ids)))
    return {ingredient_id: moved for ingredient_id, moved in rows if moved is not None}



def branch_counts(db: Session) -> dict[str, int]:
    """Across every branch, since a rename reaches all of them."""
    rows = db.execute(select(Ingredient.catalog_id, func.count()).where(Ingredient.catalog_id.is_not(None)).group_by(Ingredient.catalog_id))
    return {catalog_id: total for catalog_id, total in rows}


def names_of(db: Session, ids: set[str | None], model) -> dict[str, str]:
    wanted = [item for item in ids if item]
    if not wanted:
        return {}
    return dict(db.execute(select(model.id, model.name).where(model.id.in_(wanted))).all())


def categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).where(Category.kind == CATEGORY_KIND).order_by(Category.name)))


def units(db: Session) -> list[Unit]:
    return list(db.scalars(select(Unit).order_by(Unit.name)))


def find(db: Session, ingredient_id: str) -> Ingredient | None:
    return db.get(Ingredient, ingredient_id)


def unit_exists(db: Session, unit_id: str) -> bool:
    return db.scalar(select(Unit.id).where(Unit.id == unit_id)) is not None


def category_exists(db: Session, category_id: str) -> bool:
    return db.scalar(select(Category.id).where(Category.id == category_id, Category.kind == CATEGORY_KIND)) is not None


def named_in_branch(db: Session, outlet_id: str, name: str, except_id: str | None = None) -> Ingredient | None:
    query = select(Ingredient).where(Ingredient.outlet_id == outlet_id, func.lower(Ingredient.name) == name.lower())
    if except_id:
        query = query.where(Ingredient.id != except_id)
    return db.scalar(query.limit(1))


def linked_in_branch(db: Session, outlet_id: str, catalog_id: str) -> Ingredient | None:
    return db.scalar(select(Ingredient).where(Ingredient.outlet_id == outlet_id, Ingredient.catalog_id == catalog_id).limit(1))


def linked_to(db: Session, catalog_id: str) -> list[Ingredient]:
    return list(db.scalars(select(Ingredient).where(Ingredient.catalog_id == catalog_id)))


def catalog_named(db: Session, name: str) -> CatalogIngredient | None:
    return db.scalar(select(CatalogIngredient).where(func.lower(CatalogIngredient.name) == name.lower()))


def catalog_entry(db: Session, catalog_id: str) -> CatalogIngredient | None:
    return db.get(CatalogIngredient, catalog_id)


def branch_names(db: Session, outlet_ids: list[str]) -> list[str]:
    return list(db.scalars(select(Outlet.name).where(Outlet.id.in_(outlet_ids))))


def unit_name(db: Session, unit_id: str | None) -> str | None:
    return db.scalar(select(Unit.name).where(Unit.id == unit_id)) if unit_id else None


def impact(db: Session, ingredient_id: str) -> tuple[int, int]:
    count = lambda model, column: db.scalar(select(func.count()).select_from(model).where(column == ingredient_id)) or 0  # noqa: E731
    recipes = count(RecipeIngredient, RecipeIngredient.ingredient_id) + count(VariantChoiceRecipe, VariantChoiceRecipe.ingredient_id) + count(ExtraRecipe, ExtraRecipe.ingredient_id)
    return recipes, count(IngredientCard, IngredientCard.ingredient_id)


def delete_dependents(db: Session, ingredient_id: str) -> None:
    for model in (RecipeIngredient, VariantChoiceRecipe, ExtraRecipe, IngredientCard):
        db.execute(delete(model).where(model.ingredient_id == ingredient_id))


def active_outlets(db: Session) -> list[Outlet]:
    return list(db.scalars(select(Outlet).where(Outlet.is_active.is_(True)).order_by(Outlet.name)))


def in_branches_named(db: Session, outlet_ids: list[str], entry: CatalogIngredient) -> list[Ingredient]:
    """Ingredients that already stand for this entry: by name regardless of case, or by being linked to it."""
    return list(db.scalars(select(Ingredient).where(Ingredient.outlet_id.in_(outlet_ids), (func.lower(Ingredient.name) == entry.name.lower()) | (Ingredient.catalog_id == entry.id))))


def all_catalog(db: Session) -> list[CatalogIngredient]:
    return list(db.scalars(select(CatalogIngredient).order_by(func.lower(CatalogIngredient.name))))
