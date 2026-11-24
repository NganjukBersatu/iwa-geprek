"""What the inventory value service hands to the mappers."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class InventoryValue:
    ingredient_stock_value: Decimal
    dormant_count: int
    dormant_value: Decimal
