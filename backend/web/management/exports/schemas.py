from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core import table_export as t

WIDTH_MISMATCH = "Setiap baris harus punya jumlah kolom yang sama dengan judul kolom."


class ExportColumnIn(BaseModel):
    label: str = Field(max_length=80)
    align: Literal["left", "right"] = "left"


class ExportIn(BaseModel):
    """A table as the screen shows it; nothing is read from the database here, so what is downloaded is exactly what the person saw."""

    format: Literal["csv", "xlsx", "pdf"]
    title: str = Field(min_length=1, max_length=100)
    columns: list[ExportColumnIn] = Field(min_length=1, max_length=t.MAX_COLUMNS)
    rows: list[list[str]] = Field(max_length=t.MAX_ROWS)

    @model_validator(mode="after")
    def _same_width(self) -> "ExportIn":
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError(WIDTH_MISMATCH)
        return self
