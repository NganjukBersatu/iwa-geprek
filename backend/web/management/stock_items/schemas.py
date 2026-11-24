from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from web.management.stock_items import constants as c

Status = Literal["habis", "menipis", "aman"]


class StockItemOut(BaseModel):
    id: str
    outlet_id: str
    outlet_name: str
    menu_item_id: str
    menu_item_name: str
    unit_id: str | None
    unit: str | None
    minimum: Decimal
    is_tracked: bool
    balance: Decimal
    cost: Decimal | None = Field(description="Moving-average cost; None until a purchase with a receipt exists, which is not zero")
    inventory_value: Decimal | None = Field(description="Balance times cost; None while the cost is unknown")
    status: Status = Field(description="Worked out by the server so no screen has a threshold of its own")


class StockListOut(BaseModel):
    items: list[StockItemOut]
    total: int


class StockCandidateOut(BaseModel):
    menu_item_id: str
    menu_item_name: str
    category: str | None


class StockReceiptIn(BaseModel):
    menu_item_id: str
    qty: Decimal = Field(gt=0, description="Always positive; the server sets the sign")
    unit_price: Decimal | None = Field(None, ge=0, description="Cost per unit; left out when the delivery came without a receipt")
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)


class StockAdjustmentIn(BaseModel):
    menu_item_id: str
    qty: Decimal = Field(description="Positive adds, negative removes")
    note: str = Field(min_length=c.MIN_ADJUSTMENT_NOTE, max_length=c.MAX_NOTE_LENGTH, description="The reason, required")


class StockCountLineIn(BaseModel):
    menu_item_id: str
    counted: Decimal = Field(ge=0, description="What is physically on the shelf")


class StockCountIn(BaseModel):
    lines: list[StockCountLineIn] = Field(min_length=1)
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)


class StockCountLineOut(BaseModel):
    menu_item_id: str
    menu_item_name: str
    system_balance: Decimal
    counted: Decimal
    difference: Decimal


class StockCountOut(BaseModel):
    lines: list[StockCountLineOut]
    adjusted: int


class StockSettingsIn(BaseModel):
    """A field left out stays as it was."""

    unit_id: str | None = None
    minimum: Decimal | None = Field(None, ge=0)
    is_tracked: bool | None = None


class StockCardUpdateIn(BaseModel):
    """The kind and the item never change; another movement is written as a new row."""

    qty: Decimal | None = None
    unit_price: Decimal | None = Field(None, ge=0)
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)


class StockCardOut(BaseModel):
    id: str
    menu_item_id: str | None
    menu_item_name: str
    kind: str
    qty: Decimal
    unit_price: Decimal | None
    cost_after: Decimal | None
    order_id: str | None
    note: str | None
    user_id: str | None
    user_name: str | None
    created_at: datetime


class StockCardPageOut(BaseModel):
    items: list[StockCardOut]
    total: int
    page: int
    size: int
    balance: Decimal
