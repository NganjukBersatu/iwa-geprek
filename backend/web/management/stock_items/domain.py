from dataclasses import dataclass
from decimal import Decimal

from app.models.stock import StockItem


@dataclass(frozen=True)
class StockLine:
    item: StockItem
    outlet_name: str
    name: str
    unit: str | None
    balance: Decimal
    cost: Decimal | None
    status: str

    @property
    def inventory_value(self) -> Decimal | None:
        """None while the cost is unknown."""
        return self.balance * self.cost if self.cost is not None else None
