from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class VariantRowOut(BaseModel):
    group: str
    option: str
    menu: str | None = None
    portions: int
    transactions: int
    revenue: Decimal
    portions_percent: Decimal
    cost: Decimal | None
    margin: Decimal | None


class VariantsOut(BaseModel):
    start: date
    end: date
    by_menu: bool
    rows: list[VariantRowOut]
