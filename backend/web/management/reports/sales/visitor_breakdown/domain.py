"""What the visitor breakdown service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class VisitorGroup:
    label: str
    transactions: int
    revenue: Decimal
    percent: Decimal


@dataclass(frozen=True)
class VisitorDay:
    date: date
    transactions: int
    revenue: Decimal
    # Omzet dibagi jumlah struk hari itu; nol bila tidak ada struk.
    average_transaction: Decimal
    categories: dict[str, int]
    genders: dict[str, int]


@dataclass(frozen=True)
class VisitorBreakdown:
    start: date
    end: date
    total_transactions: int
    total_revenue: Decimal
    with_category: int
    with_gender: int
    by_category: list[VisitorGroup]
    by_gender: list[VisitorGroup]
    days: list[VisitorDay]
