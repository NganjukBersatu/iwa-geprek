"""Builds the promo usage report."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import ZERO, decimal_of
from web.management.reports.common import CENT, month_to_date, optional_percent
from web.management.reports.transactions.promos import messages, repository
from web.management.reports.transactions.promos.domain import PromoReport, PromoUsage


def promos(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> PromoReport:
    start, end = month_to_date(start, end)
    conditions = valid_orders_in(start, end, outlet_id)
    total_transactions = repository.order_count(db, conditions)
    rows = repository.discount_rows(db, conditions)
    promos_by_id = repository.promos_by_id(db, [promo_id for promo_id, *_ in rows if promo_id])

    by_promo: list[PromoUsage] = []
    promo_transactions = 0
    total_discount = Decimal("0")
    promo_revenue = Decimal("0")
    free_transactions = 0
    for promo_id, count, free, discount, revenue in rows:
        count = int(count or 0)
        free = int(free or 0)
        free_transactions += free
        discount = decimal_of(discount)
        revenue = decimal_of(revenue)
        promo_transactions += count
        total_discount += discount
        promo_revenue += revenue
        promo = promos_by_id.get(promo_id) if promo_id else None
        by_promo.append(PromoUsage(
            promo_id=promo_id,
            name=promo.name if promo else (messages.DELETED_PROMO if promo_id else messages.DISCOUNT_WITHOUT_PROMO),
            kind=promo.kind if promo else None,
            active=promo.is_active if promo else None,
            transactions=count,
            free_transactions=free,
            total_discount=discount,
            net_revenue=revenue,
            average_discount=(discount / count).quantize(CENT) if count else Decimal("0"),
        ))
    return PromoReport(
        start=start,
        end=end,
        total_transactions=total_transactions,
        promo_transactions=promo_transactions,
        free_transactions=free_transactions,
        promo_transaction_percent=optional_percent(promo_transactions, total_transactions) or ZERO,
        total_discount=total_discount,
        promo_transaction_revenue=promo_revenue,
        by_promo=by_promo,
    )
