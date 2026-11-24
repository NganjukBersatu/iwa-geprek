from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ExtraRowOut(BaseModel):
    extra: str
    quantity: int
    transactions: int
    revenue: Decimal
    revenue_percent: Decimal
    cost: Decimal | None
    profit: Decimal | None


class ExtrasOut(BaseModel):
    start: date
    end: date
    total_extra_revenue: Decimal
    total_quantity: int
    total_revenue: Decimal
    revenue_percent: Decimal
    rows: list[ExtraRowOut]
