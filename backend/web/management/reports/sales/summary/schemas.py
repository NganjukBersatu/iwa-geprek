from datetime import date
from decimal import Decimal

from web.management.reports.sales.response import CustomersOut, ResponseModel


class MethodSalesOut(ResponseModel):
    method: str
    transaction_count: int
    total: Decimal


class TopItemOut(ResponseModel):
    menu_item_id: str | None
    name: str
    qty: int
    total: Decimal


class SalesOut(ResponseModel):
    """Voided orders are in no total, but their count is shown."""

    transaction_count: int
    voided_count: int
    total: Decimal
    cash_total: Decimal
    non_cash_total: Decimal
    average_transaction: Decimal
    by_method: list[MethodSalesOut]
    top_items: list[TopItemOut]
    bottom_items: list[TopItemOut]


class ExpenseItemOut(ResponseModel):
    item_name: str
    routine_item_id: str | None
    frequency: int
    total: Decimal


class ExpensesOut(ResponseModel):
    start: date
    end: date
    total: Decimal
    drawer_cash_total: Decimal
    other_funds_total: Decimal
    transaction_count: int
    by_item: list[ExpenseItemOut]


class SalesSummaryOut(ResponseModel):
    start: date
    end: date
    sales: SalesOut
    expenses: ExpensesOut
    customers: CustomersOut
    gross_profit: Decimal
