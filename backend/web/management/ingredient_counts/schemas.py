from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.ingredients.counts import OpenState

from web.management.ingredient_counts import constants as c
from web.management.reports.inventory.ingredient_stock.schemas import IngredientStockOut


class CountLineIn(BaseModel):
    ingredient_id: str
    counted: Decimal = Field(ge=0, description="What is physically there, in the unit of the ingredient")


class OpeningIn(BaseModel):
    """The balance an ingredient had when a day began: the final figure, not a difference."""

    ingredient_id: str
    opening: Decimal = Field(ge=0, description="In the unit of the ingredient")
    from_date: date


class OpeningStatusOut(BaseModel):
    """Stok awal periode berjalan: berapa bahan aktif yang sudah diisi dari seluruhnya."""

    start: date
    filled: int
    total: int
    # Bahan yang stok awalnya belum diisi, untuk menandai barisnya di lembar opname.
    missing_ids: list[str]


class ClosingPeriodOut(BaseModel):
    """Periode cabang terakhir yang sudah selesai dan belum ditutup, atau periode berjalan bila semua sudah ditutup."""

    start: date
    end: date


class CountCloseIn(BaseModel):
    start: date
    end: date
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)
    lines: list[CountLineIn] = Field(description="Only the ingredients that were counted")


class CountOut(BaseModel):
    id: str
    outlet_id: str
    outlet_name: str
    start: date
    end: date
    note: str | None
    user_name: str | None
    ingredient_count: int
    source: str
    created_at: datetime


class DraftLineIn(BaseModel):
    ingredient_id: str
    counted: Decimal | None = Field(None, ge=0, le=Decimal("999999999"), max_digits=12, decimal_places=3, description="Empty removes the ingredient from the draft")


class CountDraftIn(BaseModel):
    lines: list[DraftLineIn] = Field(min_length=1, max_length=c.MAX_LINES)


class DraftLineOut(BaseModel):
    ingredient_id: str
    counted: Decimal
    user_name: str | None
    updated_at: datetime


class CountDraftOut(BaseModel):
    lines: list[DraftLineOut]


class RunningCountOut(BaseModel):
    """Satu bagian waktu yang belum ditutup di satu cabang, dipotong menurut periode cabang."""

    outlet_id: str
    outlet_name: str
    start: date
    # Kosong berarti periode yang sedang berjalan sampai hari ini.
    end: date | None
    state: OpenState
    # Periode cabang tempat bagian ini berada, untuk namanya.
    period_start: date
    period_end: date
    days: int
    requested: bool = Field(description="A tablet has asked to close this period and the request is still pending")


class CountLinesIn(BaseModel):
    """Counted figures to set on a closed count: an ingredient already in it is changed, one that is not is added."""

    lines: list[CountLineIn] = Field(min_length=1, max_length=c.MAX_LINES)


class CountDetailOut(CountOut):
    report: IngredientStockOut
    # False untuk bagian waktu yang ikut tertutup sebagai stok awal opname ini: tidak dihitung dan tidak bisa diubah.
    own_period: bool


class CountChangeOut(BaseModel):
    id: str
    ingredient_id: str | None
    ingredient_name: str
    action: str
    old_counted: Decimal | None
    new_counted: Decimal | None
    user_name: str | None
    created_at: datetime


class CountChangePageOut(BaseModel):
    items: list[CountChangeOut]
    total: int
    page: int
    size: int


class OpenSessionsOut(BaseModel):
    """How many cash sessions still running would put their sales into the period being closed."""

    count: int
