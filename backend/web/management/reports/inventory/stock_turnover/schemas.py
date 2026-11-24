from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from web.management.reports.inventory.stock_turnover.domain import TurnoverStatus


class TurnoverRowOut(BaseModel):
    ingredient_id: str
    name: str
    category: str | None
    unit: str
    unit_price: Decimal
    opening_stock: Decimal
    closing_stock: Decimal
    average_stock: Decimal
    sold: Decimal
    shrinkage: Decimal
    usage: Decimal
    daily_usage: Decimal
    turnover: Decimal | None
    days_of_stock: int | None
    days_since_movement: int | None
    stock_value: Decimal
    suggested_purchase: Decimal
    status: TurnoverStatus


class TurnoverOut(BaseModel):
    start: date
    end: date
    days: int
    target_days: int
    urgent_days: int
    dormant_days: int
    slow_days: int
    total_stock_value: Decimal
    out_count: int
    urgent_count: int
    dormant_count: int
    dormant_value: Decimal
    total_suggested_purchase: Decimal
    rows: list[TurnoverRowOut]
