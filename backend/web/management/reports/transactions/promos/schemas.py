from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PromoUsageOut(BaseModel):
    promo_id: str | None
    name: str
    kind: str | None
    active: bool | None
    transactions: int
    free_transactions: int
    total_discount: Decimal
    net_revenue: Decimal
    average_discount: Decimal


class PromosOut(BaseModel):
    start: date
    end: date
    total_transactions: int
    promo_transactions: int
    free_transactions: int
    promo_transaction_percent: Decimal
    total_discount: Decimal
    promo_transaction_revenue: Decimal
    by_promo: list[PromoUsageOut]
