from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class MenuMarginOut(BaseModel):
    menu_item_id: str | None
    menu_item_name: str
    qty: int
    revenue: Decimal
    cost: Decimal | None
    margin: Decimal | None
    margin_percent: Decimal | None
    cost_complete: bool


class MarginOut(BaseModel):
    start: date
    end: date
    items: list[MenuMarginOut]
    # The menus with the largest revenue, whatever order the table asked for.
    top: list[MenuMarginOut]
    total_revenue: Decimal
    total_cost: Decimal
    total_margin: Decimal
    menus_without_cost: int
    orders_without_lines: int
    revenue_without_lines: Decimal
