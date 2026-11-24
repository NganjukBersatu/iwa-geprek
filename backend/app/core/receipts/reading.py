from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ReceiptLine:
    name: str
    amount: Decimal
    quantity: int | None


@dataclass(frozen=True)
class ReceiptReading:
    """What could be read from one photo; every part may be missing, and the person checks it all before saving."""

    store: str | None
    bought_on: date | None
    total: Decimal | None
    items: tuple[ReceiptLine, ...]
    text: tuple[str, ...]
