"""What the trend service hands to the mappers."""
import enum
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class Period(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass(frozen=True)
class Bar:
    """One bar of the trend chart: its label and inclusive WIB dates."""

    label: str
    start: date
    end: date


@dataclass(frozen=True)
class TrendPoint:
    label: str
    start: date
    end: date
    income: Decimal
    expense: Decimal
    gross_profit: Decimal
    order_count: int
    average_transaction: Decimal
    customers: int
    new_customers: int
    returning_customers: int


@dataclass(frozen=True)
class Trend:
    period: Period
    start: date
    end: date
    points: list[TrendPoint]
