"""The one door for the planned cost of a recipe: ingredients, add cost, overhead and the margin left on the branch's selling price."""
import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.money import RUPIAH, ZERO, decimal_of
from app.models.cafe_settings import CafeSettings
from app.models.recipe_cost import ADD_COST_PERCENT, RecipeAddCost

CENTS = Decimal("0.01")
TENTH = Decimal("0.1")
PERCENT = 100


@dataclass(frozen=True)
class Costing:
    ingredients: Decimal | None
    add_cost_kind: str
    add_cost_value: Decimal
    add_cost_custom: bool
    add_cost: Decimal | None
    overhead: Decimal
    final_cost: Decimal | None
    target_margin_percent: Decimal | None
    target_custom: bool
    margin: Decimal | None
    margin_percent: Decimal | None
    # The price at which the margin is exactly the target: final cost divided by one minus the target, rounded to the rupiah.
    suggested_price: Decimal | None


def costing(ingredients: Decimal | None, price: Decimal, manual: RecipeAddCost | None, settings: CafeSettings | None) -> Costing:
    """Planning figures only: unlike the margin report, which uses the real cost at the time of sale, these include the add cost as a buffer."""
    custom = manual is not None and manual.kind is not None and manual.value is not None
    kind = manual.kind if custom else ADD_COST_PERCENT
    value = decimal_of(manual.value) if custom else decimal_of(settings.cost_markup_percent if settings else 0)
    overhead = decimal_of(manual.overhead) if manual is not None and manual.overhead is not None else ZERO
    target_custom = manual is not None and manual.target_margin_percent is not None
    if target_custom:
        target = decimal_of(manual.target_margin_percent)
    else:
        target = decimal_of(settings.target_margin_percent) if settings and settings.target_margin_percent is not None else None
    add_cost = None
    final_cost = None
    if ingredients is not None:
        add_cost = ((ingredients * value / PERCENT) if kind == ADD_COST_PERCENT else value).quantize(CENTS)
        final_cost = (ingredients + add_cost + overhead).quantize(CENTS)
    margin = price - final_cost if final_cost is not None else None
    margin_percent = (margin / price * PERCENT).quantize(TENTH) if margin is not None and price else None
    suggested = None
    if final_cost is not None and final_cost > 0 and target is not None and 0 < target < PERCENT:
        suggested = (final_cost / (1 - target / PERCENT)).quantize(RUPIAH, rounding=ROUND_HALF_UP)
    return Costing(ingredients, kind, value, custom, add_cost, overhead, final_cost, target, target_custom, margin, margin_percent, suggested)


def costing_of_fixed(cost: Decimal, price: Decimal, settings: CafeSettings | None) -> Costing:
    """A fixed cost is the final cost itself: no ingredients, add cost or overhead is laid on it, and only the target margin comes from the branch."""
    target = decimal_of(settings.target_margin_percent) if settings and settings.target_margin_percent is not None else None
    margin = price - cost
    margin_percent = (margin / price * PERCENT).quantize(TENTH) if price else None
    suggested = None
    if cost > 0 and target is not None and 0 < target < PERCENT:
        suggested = (cost / (1 - target / PERCENT)).quantize(RUPIAH, rounding=ROUND_HALF_UP)
    return Costing(None, ADD_COST_PERCENT, ZERO, False, None, ZERO, cost, target, False, margin, margin_percent, suggested)


def manual_of(db: Session, outlet_id: str, menu_ids: list[str]) -> dict[str, RecipeAddCost]:
    if not menu_ids:
        return {}
    rows = db.scalars(select(RecipeAddCost).where(RecipeAddCost.outlet_id == outlet_id, RecipeAddCost.menu_item_id.in_(menu_ids))).all()
    return {row.menu_item_id: row for row in rows}


def manual_of_many(db: Session, outlet_ids: list[str], menu_ids: list[str]) -> dict[tuple[str, str], RecipeAddCost]:
    """The hand-set add costs of several branches, keyed by (branch, menu), in one query."""
    if not outlet_ids or not menu_ids:
        return {}
    rows = db.scalars(select(RecipeAddCost).where(RecipeAddCost.outlet_id.in_(outlet_ids), RecipeAddCost.menu_item_id.in_(menu_ids))).all()
    return {(row.outlet_id, row.menu_item_id): row for row in rows}


def save_manual(db: Session, outlet_id: str, menu_id: str, sent: set[str], values: dict, recipe_empty: bool) -> None:
    """Each setting has three states: not sent stays, sent empty goes back to the default, a figure is set by hand; does not commit.

    The row goes when nothing is set by hand any more, and with the recipe itself, so no orphan figure comes back later.
    """
    row = manual_of(db, outlet_id, [menu_id]).get(menu_id)
    if recipe_empty:
        if row is not None:
            db.delete(row)
        return
    if not ({"add_cost_kind", "overhead", "target_margin_percent"} & sent):
        return
    if row is None:
        row = RecipeAddCost(id=str(uuid.uuid4()), outlet_id=outlet_id, menu_item_id=menu_id)
        db.add(row)
    if "add_cost_kind" in sent:
        row.kind = values.get("add_cost_kind")
        row.value = values.get("add_cost_value") if row.kind else None
    if "overhead" in sent:
        row.overhead = values.get("overhead")
    if "target_margin_percent" in sent:
        row.target_margin_percent = values.get("target_margin_percent")
    if row.kind is None and row.overhead is None and row.target_margin_percent is None:
        if row in db.new:
            db.expunge(row)
        else:
            db.delete(row)
