from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from web.management.reports.menu.highlights import HighlightOut


class BusySalesRowOut(BaseModel):
    key: str
    label: str
    occurrences: int
    transactions: int
    products: int
    customers: int
    sales: Decimal
    transactions_percent: Decimal
    products_percent: Decimal
    sales_percent: Decimal
    transactions_average: Decimal
    products_average: Decimal
    customers_average: Decimal
    sales_average: Decimal


class BusySalesOut(BaseModel):
    start: date
    end: date
    unit: str
    focus_hour: int | None
    days: int
    total_sales: Decimal
    total_transactions: int
    total_products: int
    total_customers: int
    average_per_transaction: Decimal
    transactions_without_customer: int
    highlights: list[HighlightOut]
    rows: list[BusySalesRowOut]
    # The same rows in the order the table asked for, while `rows` keeps the time axis the charts draw.
    table: list[BusySalesRowOut]
