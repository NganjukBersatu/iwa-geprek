from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.catalog.recipe_book import units_of
from app.core.orders import recipes
from app.models.order_item import OrderItem
from app.models.order_item_option import EXTRA, VARIANT, OrderItemOption

QTY_STEP = Decimal("0.001")


@dataclass(frozen=True)
class Ingredient:
    name: str
    unit: str | None
    per_portion: Decimal
    total: Decimal


@dataclass(frozen=True)
class GroupRecipe:
    portions: int
    ingredients: list[Ingredient]
    # Baris yang menunya belum punya resep di cabang ini; stasiun tetap bisa bekerja.
    without_recipe: list[str]


def of_lines(db: Session, outlet_id: str, item_ids: list[str]) -> GroupRecipe:
    items = list(db.scalars(select(OrderItem).where(OrderItem.id.in_(item_ids))).all()) if item_ids else []
    if not items:
        return GroupRecipe(portions=0, ingredients=[], without_recipe=[])
    options = list(db.scalars(select(OrderItemOption).where(OrderItemOption.order_item_id.in_([item.id for item in items]))).all())
    menus = recipes.of_menus(db, outlet_id, list({item.menu_item_id for item in items if item.menu_item_id}))
    variants = recipes.of_options(db, recipes.KIND_VARIANT, list({option.ref_id for option in options if option.kind == VARIANT and option.ref_id}), outlet_id)
    extras = recipes.of_options(db, recipes.KIND_EXTRA, list({option.ref_id for option in options if option.kind == EXTRA and option.ref_id}), outlet_id)
    options_of: dict[str, list[OrderItemOption]] = defaultdict(list)
    for option in options:
        options_of[option.order_item_id].append(option)

    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    missing: list[str] = []
    portions = 0
    for item in items:
        portions += item.qty
        menu_recipe = menus.get(item.menu_item_id or "", [])
        if not menu_recipe and item.menu_item_name not in missing:
            missing.append(item.menu_item_name)
        uses: list[tuple[list[recipes.RecipeLine], int]] = [(menu_recipe, item.qty)]
        for option in options_of.get(item.id, []):
            source = variants if option.kind == VARIANT else extras
            uses.append((source.get(option.ref_id or "", []), option.qty * item.qty))
        for lines, times in uses:
            for line in lines:
                totals[line.ingredient_id] += line.qty * times
                names[line.ingredient_id] = line.ingredient_name
    units = units_of(db, set(totals))
    ingredients = [
        Ingredient(name=names[ingredient_id], unit=units.get(ingredient_id), per_portion=(total / portions).quantize(QTY_STEP), total=total.quantize(QTY_STEP))
        for ingredient_id, total in sorted(totals.items(), key=lambda entry: names[entry[0]].lower())
    ]
    return GroupRecipe(portions=portions, ingredients=ingredients, without_recipe=missing)
