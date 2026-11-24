"""What the sales breakdown service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class BreakdownRow:
    key: str
    label: str
    transaction_count: int
    sales_total: Decimal
    average_per_transaction: Decimal
    sales_percent: Decimal
    # Empty while any line of the group has no recorded cost.
    gross_profit: Decimal | None


@dataclass(frozen=True)
class SalesBreakdown:
    start: date
    end: date
    order_types: list[BreakdownRow]
    outlets: list[BreakdownRow]
