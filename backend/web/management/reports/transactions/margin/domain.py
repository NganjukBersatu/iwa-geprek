"""What the margin service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class MenuMargin:
    menu_item_id: str | None
    menu_item_name: str
    qty: int
    revenue: Decimal
    cost: Decimal | None
    margin: Decimal | None
    margin_percent: Decimal | None
    cost_complete: bool


@dataclass(frozen=True)
class MarginReport:
    start: date
    end: date
    items: list[MenuMargin]
    total_revenue: Decimal
    total_cost: Decimal
    total_margin: Decimal
    menus_without_cost: int
    orders_without_lines: int
    revenue_without_lines: Decimal
