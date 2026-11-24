"""What the turnover service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

URGENT_DAYS = 7
SLOW_DAYS = 60
TARGET_DAYS = 14


class TurnoverStatus(str, Enum):
    OUT = "out"
    URGENT = "urgent"
    DORMANT = "dormant"
    SLOW = "slow"
    SAFE = "safe"


TURNOVER_ORDER = {
    TurnoverStatus.OUT: 0,
    TurnoverStatus.URGENT: 1,
    TurnoverStatus.DORMANT: 2,
    TurnoverStatus.SLOW: 3,
    TurnoverStatus.SAFE: 4,
}


@dataclass(frozen=True)
class TurnoverRow:
    ingredient_id: str
    name: str
    category: str | None
    unit: str
    unit_price: Decimal
    opening_stock: Decimal
    closing_stock: Decimal
    average_stock: Decimal
    sold: Decimal
    shrinkage: Decimal
    usage: Decimal
    daily_usage: Decimal
    turnover: Decimal | None
    days_of_stock: int | None
    days_since_movement: int | None
    stock_value: Decimal
    suggested_purchase: Decimal
    status: TurnoverStatus


@dataclass(frozen=True)
class Thresholds:
    target_days: int
    urgent_days: int
    dormant_days: int
    slow_days: int


@dataclass(frozen=True)
class TurnoverReport:
    start: date
    end: date
    days: int
    thresholds: Thresholds
    total_stock_value: Decimal
    out_count: int
    urgent_count: int
    dormant_count: int
    dormant_value: Decimal
    total_suggested_purchase: Decimal
    rows: list[TurnoverRow]
