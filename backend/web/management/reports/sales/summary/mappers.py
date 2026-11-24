"""Turns the summary into its response schema."""
from web.management.reports.sales.summary.domain import Summary
from web.management.reports.sales.summary.schemas import SalesSummaryOut


def summary_out(summary: Summary) -> SalesSummaryOut:
    return SalesSummaryOut.model_validate(summary)
