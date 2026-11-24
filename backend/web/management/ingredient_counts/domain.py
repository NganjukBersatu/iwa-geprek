from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CountLine:
    ingredient_id: str
    counted: Decimal


@dataclass(frozen=True)
class CountDraft:
    start: date
    end: date
    note: str | None
    lines: list[CountLine]
