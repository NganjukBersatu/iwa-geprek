"""What the kitchen service hands to the mappers."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class KitchenHour:
    hour: int
    count: int
    average_minutes: Decimal
    late: int


@dataclass(frozen=True)
class KitchenOrder:
    order_id: str
    customer_name: str | None
    table_no: str | None
    created_at: datetime
    served_at: datetime
    minutes: Decimal
    items_summary: str


@dataclass(frozen=True)
class Kitchen:
    start: date
    end: date
    threshold_minutes: int
    served_count: int
    unserved_count: int
    average_minutes: Decimal | None
    median_minutes: Decimal | None
    max_minutes: Decimal | None
    late: int
    late_percent: Decimal | None
    by_hour: list[KitchenHour]
    slowest: list[KitchenOrder]
