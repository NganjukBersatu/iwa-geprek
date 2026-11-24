from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from web.management.reports.inventory.ingredient_stock.domain import ReplacementStatus


class IngredientStockRowOut(BaseModel):
    ingredient_id: str
    name: str
    category: str | None
    unit: str
    unit_price: Decimal
    opening_stock: Decimal
    purchased: Decimal
    used: Decimal
    wasted: Decimal
    rnd: Decimal
    adjustment: Decimal
    closing_stock: Decimal
    counted: Decimal | None
    difference: Decimal | None
    shrink_percent: Decimal | None
    book_value: Decimal
    counted_value: Decimal | None
    difference_value: Decimal | None
    shrink_tolerance: Decimal
    replacement_status: ReplacementStatus


class IngredientStockOut(BaseModel):
    start: date
    end: date
    count_id: str | None
    total_replacement: Decimal | None
    total_tolerated_value: Decimal | None
    check_count: int
    rows: list[IngredientStockRowOut]
