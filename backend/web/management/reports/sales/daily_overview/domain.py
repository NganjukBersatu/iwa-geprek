"""What the daily overview service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class DailyTotals:
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


@dataclass(frozen=True)
class DailyRow(DailyTotals):
    date: date


@dataclass(frozen=True)
class DailyOverview:
    start: date
    end: date
    rows: list[DailyRow]
    total: DailyTotals
