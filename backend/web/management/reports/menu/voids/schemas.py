from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class VoidedOrderOut(BaseModel):
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


class VoidsByUserOut(BaseModel):
    username: str
    count: int
    total: Decimal


class VoidsOut(BaseModel):
    start: date
    end: date
    count: int
    total_value: Decimal
    valid_transactions: int
    void_percent: Decimal | None
    by_user: list[VoidsByUserOut]
    orders: list[VoidedOrderOut]
    page: int
    per_page: int
