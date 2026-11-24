"""What the variants service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class VariantRow:
    group: str
    option: str
    menu: str | None
    portions: int
    transactions: int
    revenue: Decimal
    portions_percent: Decimal
    cost: Decimal | None
    margin: Decimal | None


@dataclass(frozen=True)
class Variants:
    start: date
    end: date
    by_menu: bool
    rows: list[VariantRow]
