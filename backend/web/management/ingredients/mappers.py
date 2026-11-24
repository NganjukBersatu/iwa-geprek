from datetime import date
from decimal import Decimal

from app.core.http import static_url
from app.core.ingredients.stock_level import stock_level
from app.core.stock_balances import idle_days
from app.models.ingredient import Ingredient
from web.management.ingredients.constants import DORMANT_AFTER_DAYS
from web.management.ingredients.schemas import IngredientOut


def ingredient_out(
    row: Ingredient,
    base_url: str,
    *,
    balance: Decimal,
    last_move: date | None,
    branch_count: int,
    category: str | None,
    unit: str | None,
) -> IngredientOut:
    days = idle_days(last_move)
    return IngredientOut(
        id=row.id,
        outlet_id=row.outlet_id,
        catalog_id=row.catalog_id,
        branch_count=branch_count,
        name=row.name,
        category_id=row.category_id,
        category=category,
        unit_id=row.unit_id,
        unit=unit or "",
        photo_url=static_url(base_url, row.photo_path),
        package_price=row.package_price,
        package_size=row.package_size,
        unit_price=row.unit_price,
        shrink_tolerance=row.shrink_tolerance,
        minimum=row.minimum,
        is_active=row.is_active,
        is_available=row.is_available,
        balance=balance,
        stock_level=stock_level(balance, row.minimum),
        is_low=bool(row.minimum and row.minimum > 0 and balance <= row.minimum),
        days_since_move=days,
        is_dormant=bool(balance > 0 and (days is None or days >= DORMANT_AFTER_DAYS)),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
