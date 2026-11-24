"""What the ingredient stock service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class ReplacementStatus(str, Enum):
    REPLACE = "replace"
    TOLERATED = "tolerated"
    CHECK = "check"
    UNCOUNTED = "uncounted"


# Sorting by status puts what needs action first, not the text of the code.
REPLACEMENT_ORDER = (ReplacementStatus.REPLACE, ReplacementStatus.CHECK, ReplacementStatus.TOLERATED, ReplacementStatus.UNCOUNTED)

@dataclass(frozen=True)
class StockRow:
    ingredient_id: str
    name: str
    category: str | None
    unit: str
    unit_price: Decimal
    opening_stock: Decimal
    purchased: Decimal
    used: Decimal
    wasted: Decimal
    rnd: Decimal
    adjustment: Decimal
    closing_stock: Decimal
    counted: Decimal | None
    difference: Decimal | None
    shrink_percent: Decimal | None
    book_value: Decimal
    counted_value: Decimal | None
    difference_value: Decimal | None
    shrink_tolerance: Decimal
    replacement_status: ReplacementStatus


@dataclass(frozen=True)
class StockReport:
    start: date
    end: date
    count_id: str | None
    total_replacement: Decimal | None
    total_tolerated_value: Decimal | None
    check_count: int
    rows: list[StockRow]
