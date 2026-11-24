from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.core.orders.order_schemas import SessionOrderOut

MAX_LINES = 100
MAX_QTY = 999
MAX_NAME_LENGTH = 255
MAX_TABLE_LENGTH = 32
MAX_NOTE_LENGTH = 255
MAX_CLIENT_ID_LENGTH = 64
MAX_RECEIPT_LENGTH = 40
ORDER_TYPES = "^(take_away|free_table)$"


class ExtraPickIn(BaseModel):
    extra_id: str
    qty: int = Field(ge=1, le=MAX_QTY)


class OrderLineIn(BaseModel):
    menu_item_id: str
    qty: int = Field(ge=1, le=MAX_QTY)
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    variant_ids: list[str] = Field(default_factory=list)
    extras: list[ExtraPickIn] = Field(default_factory=list)


class OrderIn(BaseModel):
    """Prices, total and change are worked out on the server; the tablet sends only what was chosen."""

    client_id: str | None = Field(None, max_length=MAX_CLIENT_ID_LENGTH)
    # Only for a sale queued while offline: the session it was sold in and the real time of the sale.
    session_id: str | None = None
    created_at: datetime | None = None
    order_type: str = Field(pattern=ORDER_TYPES)
    customer_name: str | None = Field(None, max_length=MAX_NAME_LENGTH)
    table_no: str | None = Field(None, max_length=MAX_TABLE_LENGTH)
    # Left out only for an open bill, which is paid later.
    payment_method: str | None = None
    cash_received: Decimal | None = Field(None, ge=0)
    receipt_number: str | None = Field(None, max_length=MAX_RECEIPT_LENGTH)
    items: list[OrderLineIn] = Field(min_length=1, max_length=MAX_LINES)
    # Optional notes for the reports; a stale choice is dropped, never a reason to refuse the sale.
    visitor_category_id: str | None = None
    visitor_gender_id: str | None = None
    # A registered customer picked from the suggestions, and a note on the whole order; a stale customer is dropped the same way.
    customer_id: str | None = None
    note_id: str | None = None
    # The words of the picked note, kept on the order when the note was deleted before the sale reached the server.
    note_label: str | None = Field(None, max_length=MAX_NAME_LENGTH)
    # One promo per order; the server works the discount out itself.
    promo_id: str | None = None
    # Written and sent to the stations now, paid later; the promo and the method are chosen when it is paid.
    open_bill: bool = False

    @model_validator(mode="after")
    def _method_unless_open(self) -> "OrderIn":
        if not self.open_bill and not self.payment_method:
            raise ValueError("payment_method is required for a bill that is paid now")
        if self.open_bill and (self.created_at is not None or self.session_id is not None):
            raise ValueError("an open bill is written live, never from the offline queue")
        return self


class OrderOut(BaseModel):
    id: str
    receipt_number: str | None
    total: Decimal
    cash_received: Decimal | None
    payment_method_label: str | None
    created_at: datetime


class ReceiptNumberOut(BaseModel):
    receipt_number: str


class OpenBillOut(SessionOrderOut):
    """A bill not paid yet: who rang it up, and whether the asking cashier owns its session."""

    cashier_name: str | None
    mine: bool


class BillLinesIn(BaseModel):
    version: int = Field(ge=1, description="The version of the bill the cashier saw; a changed bill is refused")
    items: list[OrderLineIn] = Field(min_length=1, max_length=MAX_LINES)


class BillSettleIn(BaseModel):
    version: int = Field(ge=1)
    payment_method: str
    cash_received: Decimal | None = Field(None, ge=0)
    promo_id: str | None = None
    settle_key: str = Field(min_length=8, max_length=MAX_CLIENT_ID_LENGTH, description="Random key per payment; a resend returns the first payment")


class BillQuoteIn(BaseModel):
    promo_id: str | None = None


class BillQuoteOut(BaseModel):
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    promo_name: str | None


class BillCancelIn(BaseModel):
    reason: str | None = Field(None, max_length=MAX_NAME_LENGTH)
