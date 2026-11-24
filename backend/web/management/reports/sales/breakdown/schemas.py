from datetime import date
from decimal import Decimal

from web.management.reports.sales.response import ResponseModel


class BreakdownRowOut(ResponseModel):
    key: str
    label: str
    transaction_count: int
    sales_total: Decimal
    average_per_transaction: Decimal
    sales_percent: Decimal
    gross_profit: Decimal | None


class SalesBreakdownOut(ResponseModel):
    start: date
    end: date
    order_types: list[BreakdownRowOut]
    # Empty when one branch is chosen: there is nothing to compare.
    outlets: list[BreakdownRowOut]
