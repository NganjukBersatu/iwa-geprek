from datetime import date, datetime

from pydantic import BaseModel, Field


class IngredientCountRequestIn(BaseModel):
    note: str | None = Field(None, max_length=255)


class IngredientCountRequestOut(BaseModel):
    seen_by: str | None
    seen_at: datetime | None
    # Rentang yang ditutup bila disetujui: periode penutupan bila sudah ditutup, selain itu periode yang harus ditutup berikutnya.
    close_start: date
    close_end: date
    id: str
    outlet_id: str
    outlet_name: str
    period_start: date
    status: str
    note: str | None
    requested_by: str | None
    decided_by: str | None
    decided_at: datetime | None
    count_id: str | None
    created_at: datetime
    opening_filled: int = Field(description="Bahan aktif cabang yang stok awal periode ini sudah diisi")
    opening_total: int = Field(description="Bahan aktif cabang ini")


class IngredientCountRequestPageOut(BaseModel):
    items: list[IngredientCountRequestOut]
    total: int = Field(description="Every pending request in scope, not only this page")
    page: int
    size: int
