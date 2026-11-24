from decimal import Decimal

from pydantic import BaseModel

from web.management.reports.inventory.low_stock.domain import LowStockKind, LowStockLevel


class LowStockItemOut(BaseModel):
    kind: LowStockKind
    id: str
    name: str
    category: str | None
    unit: str
    balance: Decimal
    minimum: Decimal
    average_daily_usage: Decimal
    days_until_empty: Decimal | None
    level: LowStockLevel


class LowStockOut(BaseModel):
    count: int
    items: list[LowStockItemOut]
