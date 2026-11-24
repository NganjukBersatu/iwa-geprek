"""What the busy-sales service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from web.management.reports.menu.highlights import Highlight
from web.management.reports.menu.time_slots import TimeSlot


@dataclass(frozen=True)
class BusySalesRow:
    slot: TimeSlot
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


@dataclass(frozen=True)
class BusySales:
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
    highlights: list[Highlight]
    rows: list[BusySalesRow]
