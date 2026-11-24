"""What the transaction list service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.order import Order


@dataclass(frozen=True)
class MethodTotal:
    code: str
    label: str
    count: int
    amount: Decimal


@dataclass(frozen=True)
class TransactionPage:
    start: date
    end: date
    group: str
    method: str | None
    count: int
    amount: Decimal
    by_method: list[MethodTotal]
    page: int
    per_page: int
    orders: list[Order]
    cashier_names: dict[str, str]
