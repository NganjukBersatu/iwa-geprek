from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from web.management.reports.menu.highlights import HighlightOut


class TimeSlotOut(BaseModel):
    key: str
    label: str
    occurrences: int


class ProductSeriesOut(BaseModel):
    menu_item_name: str
    total_qty: int
    total_revenue: Decimal
    values: list[int]


class BusyProductRowOut(BaseModel):
    menu_item_name: str
    key: str
    label: str
    qty: int
    qty_percent: Decimal
    transactions: int
    transactions_percent: Decimal
    revenue: Decimal
    revenue_percent: Decimal


class BusyProductsOut(BaseModel):
    start: date
    end: date
    unit: str
    focus_hour: int | None
    days: int
    slots: list[TimeSlotOut]
    series: list[ProductSeriesOut]
    total_qty: int
    total_revenue: Decimal
    total_transactions: int
    orders_without_lines: int
    revenue_without_lines: Decimal
    product_count: int
    top_product: str | None
    top_product_percent: Decimal
    highlights: list[HighlightOut]
    rows: list[BusyProductRowOut]
    total_rows: int
    page: int
    per_page: int
