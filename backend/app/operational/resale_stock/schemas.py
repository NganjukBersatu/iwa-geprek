from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.operational.resale_stock.constants import MAX_COUNT_LINES, MAX_NOTE_LENGTH, MIN_ADJUSTMENT_NOTE

QUANTITY = Field(gt=0, le=Decimal("999999999"), max_digits=12, decimal_places=3, description="Selalu positif; tanda diatur server")


class TabletResaleItemOut(BaseModel):
    menu_item_id: str
    name: str
    unit: str | None
    stock: Decimal
    minimum: Decimal
    status: str = Field(description="habis, menipis, atau aman; dihitung server")


class TabletResaleItemPageOut(BaseModel):
    items: list[TabletResaleItemOut]
    total: int
    page: int
    size: int


class TabletResaleReceiptIn(BaseModel):
    menu_item_id: str = Field(min_length=1)
    qty: Decimal = QUANTITY
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class TabletResaleAdjustmentIn(BaseModel):
    menu_item_id: str = Field(min_length=1)
    qty: Decimal = Field(le=Decimal("999999999"), ge=Decimal("-999999999"), max_digits=12, decimal_places=3, description="Positif menambah, negatif mengurangi")
    note: str = Field(min_length=MIN_ADJUSTMENT_NOTE, max_length=MAX_NOTE_LENGTH, description="Alasan, wajib")


class TabletResaleMovementOut(BaseModel):
    id: str
    menu_item_name: str
    unit: str | None
    qty: Decimal
    kind: str
    note: str | None
    user_name: str | None
    created_at: datetime


class TabletResaleMovementPageOut(BaseModel):
    items: list[TabletResaleMovementOut]
    total: int
    page: int
    size: int


class TabletResaleCountLineIn(BaseModel):
    menu_item_id: str = Field(min_length=1)
    counted: Decimal = Field(ge=0, le=Decimal("999999999"), max_digits=12, decimal_places=3, description="Yang benar-benar ada di rak")


class TabletResaleCountIn(BaseModel):
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    lines: list[TabletResaleCountLineIn] = Field(min_length=1, max_length=MAX_COUNT_LINES, description="Hanya barang yang dihitung")


class TabletResaleCountOut(BaseModel):
    counted: int
    adjusted: int
