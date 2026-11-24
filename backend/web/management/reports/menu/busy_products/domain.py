"""What the busy-products service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from web.management.reports.menu.highlights import Highlight
from web.management.reports.menu.time_slots import TimeSlot


@dataclass(frozen=True)
class ProductSeries:
    menu_item_name: str
    total_qty: int
    total_revenue: Decimal
    values: list[int]


@dataclass(frozen=True)
class BusyProductRow:
    menu_item_name: str
    key: str
    label: str
    qty: int
    qty_percent: Decimal
    transactions: int
    transactions_percent: Decimal
    revenue: Decimal
    revenue_percent: Decimal


@dataclass(frozen=True)
class BusyProducts:
    start: date
    end: date
    unit: str
    focus_hour: int | None
    days: int
    slots: list[TimeSlot]
    series: list[ProductSeries]
    total_qty: int
    total_revenue: Decimal
    total_transactions: int
    orders_without_lines: int
    revenue_without_lines: Decimal
    product_count: int
    top_product: str | None
    top_product_percent: Decimal
    highlights: list[Highlight]
    rows: list[BusyProductRow]
    total_rows: int
    page: int
    per_page: int
