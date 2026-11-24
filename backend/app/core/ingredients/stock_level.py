"""Satu aturan penanda stok bahan yang dipakai web admin dan tablet."""
from decimal import Decimal
from enum import StrEnum


class StockLevel(StrEnum):
    NEGATIVE = "negative"
    OUT = "out"
    LOW = "low"


def stock_level(balance: Decimal, minimum: Decimal) -> StockLevel | None:
    """Minus di bawah nol, habis di nol, dan menipis hanya bila minimum terisi dan stok masih ada."""
    if balance < 0:
        return StockLevel.NEGATIVE
    if balance == 0:
        return StockLevel.OUT
    if minimum > 0 and balance <= minimum:
        return StockLevel.LOW
    return None
