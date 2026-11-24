"""What the comparison service hands to the mappers."""
import enum
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class ComparisonMode(str, enum.Enum):
    AUTO = "auto"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    CUSTOM = "custom"


@dataclass(frozen=True)
class Metric:
    current: Decimal
    previous: Decimal
    difference: Decimal
    percent: Decimal | None


@dataclass(frozen=True)
class Comparison:
    start: date
    end: date
    mode: ComparisonMode
    previous_start: date
    previous_end: date
    comparison_label: str
    cut_off_at: str | None
    income: Metric
    expense: Metric
    transactions: Metric
    # Pemasukan dibagi jumlah struk, supaya terlihat pertumbuhan datang dari struk lebih banyak atau nilai struk lebih besar.
    average_transaction: Metric
    customers: Metric
    profit: Metric
