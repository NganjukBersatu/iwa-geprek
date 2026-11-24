from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.operational.stock.constants import MAX_NOTE_LENGTH

QUANTITY = Field(gt=0, le=Decimal("999999999"), max_digits=12, decimal_places=3, description="In the unit of the ingredient")


class TabletStockIngredientOut(BaseModel):
    id: str
    name: str
    unit: str | None
    category: str | None
    stock: Decimal
    minimum: Decimal
    opening: Decimal | None = Field(description="Stok awal periode berjalan; kosong berarti belum diisi")
    package_size: Decimal = Field(description="Isi satu kemasan beli dalam satuan bahan; 1 atau kurang berarti tanpa kemasan")


class TabletStockIngredientPageOut(BaseModel):
    items: list[TabletStockIngredientOut]
    total: int
    page: int
    size: int


class TabletStockCauseOut(BaseModel):
    code: str
    label: str


class TabletStockReceiptIn(BaseModel):
    ingredient_id: str = Field(min_length=1)
    qty: Decimal = QUANTITY
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class TabletStockWasteIn(TabletStockReceiptIn):
    cause: str = Field(min_length=1)


class TabletStockTrialIn(BaseModel):
    ingredient_id: str = Field(min_length=1)
    qty: Decimal = QUANTITY
    note: str = Field(min_length=1, max_length=MAX_NOTE_LENGTH)


class TabletStockMovementUpdateIn(BaseModel):
    """A field left out stays as it was; the direction of a movement never flips."""

    qty: Decimal | None = Field(None, gt=0, le=Decimal("999999999"), max_digits=12, decimal_places=3, description="The size; its sign follows the kind of the movement")
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class TabletStockMovementOut(BaseModel):
    id: str
    ingredient_id: str | None
    ingredient_name: str
    unit: str | None
    qty: Decimal
    kind: str
    cause_label: str | None
    note: str | None
    user_name: str | None
    created_at: datetime
    proof_url: str | None = Field(None, description="Foto nota atau bukti; kosong bila belum dilampirkan")
    from_sale: bool = Field(description="Written by a sale; it cannot be corrected or removed")
    from_count: bool = Field(description="Written by closing a count; it can be corrected but not removed")
    from_opening: bool = Field(description="Stok awal periode; diubah atau dihapus lewat kartu stok awal, bukan dari riwayat")


class TabletStockMovementPageOut(BaseModel):
    items: list[TabletStockMovementOut]
    total: int
    page: int
    size: int


class TabletStockRequestOut(BaseModel):
    status: str = Field(description="pending, rejected, atau closed")
    note: str | None
    requested_by: str | None
    created_at: datetime
    decided_by: str | None
    decided_at: datetime | None


class TabletStockOpeningPeriodOut(BaseModel):
    start: date
    close_start: date = Field(description="Awal rentang yang ditutup berikutnya, sama dengan web (periode cabang)")
    close_end: date = Field(description="Akhir rentang yang ditutup berikutnya; hari ini bila periode berjalan belum selesai")
    filled: int = Field(description="Bahan aktif yang stok awal periodenya sudah diisi")
    total: int = Field(description="Bahan aktif cabang")
    request: TabletStockRequestOut | None = Field(description="Pengajuan tutup periode terakhir untuk periode ini")


class TabletStockJourneyOut(BaseModel):
    start: date
    opening: Decimal
    opening_set: bool
    opening_by: str | None
    opening_at: datetime | None
    received: Decimal
    sold: Decimal
    wasted: Decimal
    trial: Decimal
    adjusted: Decimal
    stock: Decimal


class TabletStockOpeningIn(BaseModel):
    qty: Decimal = Field(ge=0, le=Decimal("999999999"), max_digits=12, decimal_places=3, description="Stok awal dalam satuan bahan")


class TabletStockOpeningRowIn(BaseModel):
    """One row of filling many openings at once from the tablet; the branch and period come from the tablet, never from the row."""

    ingredient_id: str = Field(min_length=1, max_length=64)
    qty: Decimal = Field(ge=0, le=Decimal("999999999"), max_digits=12, decimal_places=3, description="Stok awal dalam satuan bahan")


class TabletStockCloseRequestIn(BaseModel):
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class TabletStockRecipeUseOut(BaseModel):
    menu_item_id: str
    menu_name: str
    qty: Decimal = Field(description="Takaran per porsi dalam satuan bahan")


class TabletStockRecipeUsePageOut(BaseModel):
    items: list[TabletStockRecipeUseOut]
    total: int
    page: int
    size: int