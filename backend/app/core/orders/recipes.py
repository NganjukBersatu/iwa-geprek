"""Recipes of a menu item, a variant choice or an extra, their cost, and the ingredients a sale uses up."""
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.money import decimal_of
from app.models.extra import ExtraRecipe
from app.models.ingredient import INGREDIENT_OUT, Ingredient, IngredientCard, RecipeIngredient
from app.models.variant import VariantChoiceRecipe

CENTS = Decimal("0.01")
KIND_VARIANT = "varian"
KIND_EXTRA = "ekstra"


@dataclass(frozen=True)
class RecipeLine:
    ingredient_id: str
    ingredient_name: str
    qty: Decimal
    unit_price: Decimal


def _lines(db: Session, rows: list[tuple[str, str, Decimal]]) -> dict[str, list[RecipeLine]]:
    """`rows` are (owner id, ingredient id, qty); names and prices come from the ingredients in one query."""
    if not rows:
        return {}
    ingredients = {item.id: item for item in db.scalars(select(Ingredient).where(Ingredient.id.in_({row[1] for row in rows}))).all()}
    result: dict[str, list[RecipeLine]] = {}
    for owner_id, ingredient_id, qty in rows:
        ingredient = ingredients.get(ingredient_id)
        if ingredient is None:
            continue
        result.setdefault(owner_id, []).append(RecipeLine(ingredient.id, ingredient.name, decimal_of(qty), decimal_of(ingredient.unit_price)))
    return result


def of_menus(db: Session, outlet_id: str, menu_ids: list[str]) -> dict[str, list[RecipeLine]]:
    """The recipes of every menu item on one order, in one query."""
    if not menu_ids:
        return {}
    rows = db.execute(
        select(RecipeIngredient.menu_item_id, RecipeIngredient.ingredient_id, RecipeIngredient.qty).where(
            RecipeIngredient.outlet_id == outlet_id, RecipeIngredient.menu_item_id.in_(menu_ids)
        )
    ).all()
    return _lines(db, [tuple(row) for row in rows])


def of_menus_many(db: Session, outlet_ids: list[str], menu_ids: list[str]) -> dict[tuple[str, str], list[RecipeLine]]:
    """The recipes of the menu items at several branches, keyed by (branch, menu): two queries however many branches."""
    if not outlet_ids or not menu_ids:
        return {}
    rows = db.execute(
        select(RecipeIngredient.outlet_id, RecipeIngredient.menu_item_id, RecipeIngredient.ingredient_id, RecipeIngredient.qty).where(
            RecipeIngredient.outlet_id.in_(outlet_ids), RecipeIngredient.menu_item_id.in_(menu_ids)
        )
    ).all()
    if not rows:
        return {}
    ingredients = {item.id: item for item in db.scalars(select(Ingredient).where(Ingredient.id.in_({row[2] for row in rows}))).all()}
    result: dict[tuple[str, str], list[RecipeLine]] = {}
    for outlet_id, menu_id, ingredient_id, qty in rows:
        ingredient = ingredients.get(ingredient_id)
        if ingredient is not None:
            result.setdefault((outlet_id, menu_id), []).append(RecipeLine(ingredient.id, ingredient.name, decimal_of(qty), decimal_of(ingredient.unit_price)))
    return result


def of_options(db: Session, kind: str, owner_ids: list[str], outlet_id: str) -> dict[str, list[RecipeLine]]:
    """Extra ingredients of variant choices or extras at one branch."""
    if not owner_ids:
        return {}
    if kind == KIND_VARIANT:
        statement = select(VariantChoiceRecipe.choice_id, VariantChoiceRecipe.ingredient_id, VariantChoiceRecipe.qty).where(
            VariantChoiceRecipe.choice_id.in_(owner_ids), VariantChoiceRecipe.outlet_id == outlet_id
        )
    else:
        statement = select(ExtraRecipe.extra_id, ExtraRecipe.ingredient_id, ExtraRecipe.qty).where(
            ExtraRecipe.extra_id.in_(owner_ids), ExtraRecipe.outlet_id == outlet_id
        )
    return _lines(db, [tuple(row) for row in db.execute(statement).all()])


def cost_of(lines: list[RecipeLine]) -> Decimal | None:
    """Cost of one portion; None without a recipe, because unknown and zero are different news."""
    if not lines:
        return None
    return sum((line.qty * line.unit_price for line in lines), Decimal(0)).quantize(CENTS)


def use_up(db: Session, outlet_id: str, order_id: str, user_id: str | None, usages: list[tuple[list[RecipeLine], int]]) -> None:
    """One outgoing card per ingredient; a menu without a recipe is skipped so selling never fails for want of one."""
    for lines, portions in usages:
        for line in lines:
            db.add(
                IngredientCard(
                    id=str(uuid.uuid4()),
                    outlet_id=outlet_id,
                    ingredient_id=line.ingredient_id,
                    ingredient_name=line.ingredient_name,
                    kind=INGREDIENT_OUT,
                    qty=-(line.qty * portions),
                    unit_price=None,
                    order_id=order_id,
                    user_id=user_id,
                    created_at=clock.now(),
                )
            )
