from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class IngredientDraft:
    name: str
    unit_id: str
    category_id: str | None
    package_price: Decimal
    package_size: Decimal
    unit_price: Decimal | None
    shrink_tolerance: Decimal
    minimum: Decimal
