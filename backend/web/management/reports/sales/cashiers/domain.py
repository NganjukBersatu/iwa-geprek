"""What the cashier report service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CashierRow:
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


@dataclass(frozen=True)
class CashierReport:
    start: date
    end: date
    cashiers: list[CashierRow]
