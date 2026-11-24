"""Turns the customer report into its response schema."""
from web.management.reports.sales.customers.domain import CustomerReport
from web.management.reports.sales.customers.schemas import CustomerReportOut


def customer_report_out(report: CustomerReport) -> CustomerReportOut:
    return CustomerReportOut.model_validate(report)
