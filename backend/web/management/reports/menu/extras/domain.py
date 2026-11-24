"""What the extras service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ExtraRow:
    extra: str
    quantity: int
    transactions: int
    revenue: Decimal
    revenue_percent: Decimal
    cost: Decimal | None
    profit: Decimal | None


@dataclass(frozen=True)
class Extras:
    start: date
    end: date
    total_extra_revenue: Decimal
    total_quantity: int
    total_revenue: Decimal
    revenue_percent: Decimal
    rows: list[ExtraRow]
