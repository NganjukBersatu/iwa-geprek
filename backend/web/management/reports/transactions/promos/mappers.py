"""Turns the promo report into its response schema."""
from dataclasses import asdict

from app.core.sorting import RowSorting
from web.management.reports.transactions.promos.domain import PromoReport, PromoUsage
from web.management.reports.transactions.promos.schemas import PromosOut, PromoUsageOut


SORTING: RowSorting[PromoUsage] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "transactions": lambda row: row.transactions,
        "free": lambda row: row.free_transactions,
        "discount": lambda row: row.total_discount,
        "average": lambda row: row.average_discount,
        "net_revenue": lambda row: row.net_revenue,
    },
    identity=lambda row: f"{row.name}|{row.promo_id or ''}",
)


def promos_out(report: PromoReport, sort: str | None) -> PromosOut:
    return PromosOut(
        start=report.start,
        end=report.end,
        total_transactions=report.total_transactions,
        promo_transactions=report.promo_transactions,
        free_transactions=report.free_transactions,
        promo_transaction_percent=report.promo_transaction_percent,
        total_discount=report.total_discount,
        promo_transaction_revenue=report.promo_transaction_revenue,
        by_promo=[PromoUsageOut(**asdict(usage)) for usage in SORTING.apply(report.by_promo, sort)],
    )
