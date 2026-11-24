"""Ingredient movements read by both the ingredient stock and the turnover reports; balances come from app.core.stock_balances."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.money import decimal_of
from app.models.ingredient import IngredientCard
from app.core.branches import branch_filter
from app.core.business_days import within
from app.core.ingredients.openings import is_opening


def card_filter(outlet_id: str | None) -> tuple:
    return (IngredientCard.ingredient_id.is_not(None), *branch_filter(IngredientCard.outlet_id, outlet_id))


def movements_by_kind(
    db: Session, outlet_id: str | None, start: date, end: date, *, skip_count_cards: bool
) -> dict[str, dict[str, Decimal]]:
    """Signed movement per ingredient and kind; `skip_count_cards` leaves out the adjustments a closed count wrote."""
    conditions = [*within(IngredientCard.business_day, start, end), *card_filter(outlet_id)]
    if skip_count_cards:
        conditions.append(IngredientCard.count_id.is_(None))
        # Stok awal periode berikutnya dicap detik terakhir periode ini, jadi bukan pergerakan periode ini.
        conditions.append(~func.coalesce(is_opening(end + timedelta(days=1)), False))
    rows = db.execute(
        select(IngredientCard.ingredient_id, IngredientCard.kind, func.coalesce(func.sum(IngredientCard.qty), 0))
        .where(*conditions)
        .group_by(IngredientCard.ingredient_id, IngredientCard.kind)
    ).all()
    movements: dict[str, dict[str, Decimal]] = {}
    for ingredient_id, kind, qty in rows:
        movements.setdefault(ingredient_id, {})[kind] = decimal_of(qty)
    return movements
