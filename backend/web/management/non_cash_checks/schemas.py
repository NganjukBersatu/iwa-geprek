from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from web.management.reports.sales.response import ResponseModel

CheckStatus = Literal["pending", "balanced", "mismatch"]


class NonCashCheckRowOut(ResponseModel):
    outlet_id: str
    outlet_name: str
    date: date
    recorded: Decimal
    bank_amount: Decimal | None
    difference: Decimal | None
    status: CheckStatus


class NonCashCheckSummaryOut(ResponseModel):
    balanced: int
    mismatch: int
    pending: int
    total_difference: Decimal


class NonCashChecksOut(ResponseModel):
    outlet_id: str | None
    start: date
    end: date
    # Labels of the non-cash methods open in the branches shown, for the titles of the panel.
    methods: list[str]
    rows: list[NonCashCheckRowOut]
    summary: NonCashCheckSummaryOut


class NonCashCheckIn(BaseModel):
    bank_amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
