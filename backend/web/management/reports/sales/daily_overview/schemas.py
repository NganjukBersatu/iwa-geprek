from datetime import date
from decimal import Decimal

from web.management.reports.sales.response import ResponseModel


class DailyTotalsOut(ResponseModel):
    cash_income: Decimal
    non_cash_income: Decimal
    income_total: Decimal
    cash_expense: Decimal
    non_cash_expense: Decimal
    expense_total: Decimal
    expense_percent: Decimal
    cash_profit: Decimal
    non_cash_profit: Decimal
    profit_total: Decimal
    profit_percent: Decimal


class DailyRowOut(DailyTotalsOut):
    date: date


class DailyOverviewOut(ResponseModel):
    start: date
    end: date
    rows: list[DailyRowOut]
    total: DailyTotalsOut
