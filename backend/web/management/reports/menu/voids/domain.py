"""What the voids service hands to the mappers."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class VoidedOrder:
    order_id: str
    created_at: datetime
    voided_at: datetime
    customer_name: str | None
    table_no: str | None
    total: Decimal
    reason: str | None
    cashier_username: str | None
    voided_by: str | None
    items_summary: str


@dataclass(frozen=True)
class VoidsByUser:
    username: str
    count: int
    total: Decimal


@dataclass(frozen=True)
class Voids:
    start: date
    end: date
    count: int
    total_value: Decimal
    valid_transactions: int
    void_percent: Decimal | None
    by_user: list[VoidsByUser]
    orders: list[VoidedOrder]
    page: int
    per_page: int
