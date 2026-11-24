from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class KitchenHourOut(BaseModel):
    hour: int
    count: int
    average_minutes: Decimal
    late: int


class KitchenOrderOut(BaseModel):
    order_id: str
    customer_name: str | None
    table_no: str | None
    created_at: datetime
    served_at: datetime
    minutes: Decimal
    items_summary: str


class KitchenOut(BaseModel):
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
    by_hour: list[KitchenHourOut]
    # The hour with the most orders, the earliest on a tie, whatever order by_hour was asked in.
    busiest_hour: KitchenHourOut | None
    slowest: list[KitchenOrderOut]
