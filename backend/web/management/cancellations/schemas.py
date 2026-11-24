from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.orders.cancellations import MAX_NOTE_LENGTH


class CancellationDecisionIn(BaseModel):
    approve: bool
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class CancellationOut(BaseModel):
    id: str
    outlet_id: str
    outlet_name: str
    order_id: str
    receipt_number: str | None
    customer_name: str | None
    table_no: str | None
    order_total: Decimal
    order_created_at: datetime
    order_business_day: date
    items_summary: str
    cashier: str
    requested_by: str
    reason: str | None
    created_at: datetime


class CancellationPageOut(BaseModel):
    items: list[CancellationOut]
    total: int = Field(description="Every waiting request in scope, not only this page")
    page: int
    size: int
