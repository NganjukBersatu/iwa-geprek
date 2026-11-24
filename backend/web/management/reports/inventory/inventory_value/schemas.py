from decimal import Decimal

from pydantic import BaseModel


class InventoryValueOut(BaseModel):
    ingredient_stock_value: Decimal
    dormant_count: int
    dormant_value: Decimal
