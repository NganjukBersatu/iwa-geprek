"""What the summary service hands to the mappers."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from web.management.reports.sales.visitors import Customers


@dataclass(frozen=True)
class MethodSales:
    method: str
    transaction_count: int
    total: Decimal


@dataclass(frozen=True)
class TopItem:
    menu_item_id: str | None
    name: str
    qty: int
    total: Decimal


@dataclass(frozen=True)
class Sales:
    transaction_count: int
    voided_count: int
    total: Decimal
    cash_total: Decimal
    non_cash_total: Decimal
    average_transaction: Decimal
    by_method: list[MethodSales]
    top_items: list[TopItem]
    bottom_items: list[TopItem]


@dataclass(frozen=True)
class ExpenseItem:
    item_name: str
    routine_item_id: str | None
    frequency: int
    total: Decimal


@dataclass(frozen=True)
class Expenses:
    start: date
    end: date
    total: Decimal
    drawer_cash_total: Decimal
    other_funds_total: Decimal
    transaction_count: int
    by_item: list[ExpenseItem]


@dataclass(frozen=True)
class Summary:
    start: date
    end: date
    sales: Sales
    expenses: Expenses
    customers: Customers
    gross_profit: Decimal
