from datetime import date
from decimal import Decimal

from web.management.reports.sales.response import ResponseModel


class CashierRowOut(ResponseModel):
    cashier_id: str
    username: str
    transaction_count: int
    voided_count: int
    sales_total: Decimal
    cash_total: Decimal
    non_cash_total: Decimal
    expense_total: Decimal
    session_count: int
    difference_total: Decimal


class CashierReportOut(ResponseModel):
    start: date
    end: date
    cashiers: list[CashierRowOut]
