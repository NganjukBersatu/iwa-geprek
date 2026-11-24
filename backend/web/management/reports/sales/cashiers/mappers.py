"""Turns the cashier report into its response schema."""
from dataclasses import replace

from app.core.sorting import RowSorting
from web.management.reports.sales.cashiers.domain import CashierReport, CashierRow
from web.management.reports.sales.cashiers.schemas import CashierReportOut

SORTING: RowSorting[CashierRow] = RowSorting(
    keys={
        "cashier": lambda row: row.username,
        "transactions": lambda row: row.transaction_count,
        "sales": lambda row: row.sales_total,
        "expenses": lambda row: row.expense_total,
        # A cashier with no closed session has no difference yet and sorts last.
        "difference": lambda row: row.difference_total if row.session_count else None,
    },
    identity=lambda row: row.cashier_id,
)


def cashier_report_out(report: CashierReport, sort: str | None) -> CashierReportOut:
    return CashierReportOut.model_validate(replace(report, cashiers=SORTING.apply(report.cashiers, sort)))
