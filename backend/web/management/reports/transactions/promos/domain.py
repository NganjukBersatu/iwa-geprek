"""What the promo service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class PromoUsage:
    promo_id: str | None
    name: str
    kind: str | None
    active: bool | None
    transactions: int
    # Struk berpromo yang totalnya nol (potongan 100%); ikut menurunkan nilai struk rata-rata.
    free_transactions: int
    total_discount: Decimal
    net_revenue: Decimal
    average_discount: Decimal


@dataclass(frozen=True)
class PromoReport:
    start: date
    end: date
    total_transactions: int
    promo_transactions: int
    free_transactions: int
    promo_transaction_percent: Decimal
    total_discount: Decimal
    promo_transaction_revenue: Decimal
    by_promo: list[PromoUsage]
