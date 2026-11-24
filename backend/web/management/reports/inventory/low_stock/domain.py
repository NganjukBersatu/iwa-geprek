"""What the low stock service hands to the mappers."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

LOW_STOCK_WINDOW_DAYS = 7
LOW_STOCK_SOON_DAYS = 2


class LowStockLevel(str, Enum):
    OUT = "out"
    LOW = "low"
    SOON = "soon"


class LowStockKind(str, Enum):
    INGREDIENT = "ingredient"
    RESALE = "resale"


LOW_STOCK_ORDER = {LowStockLevel.OUT: 0, LowStockLevel.LOW: 1, LowStockLevel.SOON: 2}


@dataclass(frozen=True)
class LowStockItem:
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
