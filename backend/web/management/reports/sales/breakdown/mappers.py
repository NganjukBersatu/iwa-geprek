"""Turns the sales breakdown into its response schema."""
from dataclasses import replace

from app.core.sorting import RowSorting
from web.management.reports.sales.breakdown.domain import BreakdownRow, SalesBreakdown
from web.management.reports.sales.breakdown.schemas import SalesBreakdownOut

SORTING: RowSorting[BreakdownRow] = RowSorting(
    keys={
        "name": lambda row: row.label,
        "transactions": lambda row: row.transaction_count,
        "sales": lambda row: row.sales_total,
        "average": lambda row: row.average_per_transaction,
        "profit": lambda row: row.gross_profit,
    },
    identity=lambda row: row.key,
)


def sales_breakdown_out(report: SalesBreakdown, type_sort: str | None, outlet_sort: str | None) -> SalesBreakdownOut:
    return SalesBreakdownOut.model_validate(
        replace(
            report,
            order_types=SORTING.apply(report.order_types, type_sort),
            outlets=SORTING.apply(report.outlets, outlet_sort),
        )
    )
