"""Builds the summary; figures, rounding, and ordering match the legacy /laporan routes exactly."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.money import RUPIAH
from app.models.order import CASH_METHOD
from web.management.reports.common import from_today
from web.management.reports.sales.summary import repository
from web.management.reports.sales.summary.domain import ExpenseItem, Expenses, MethodSales, Sales, Summary, TopItem
from web.management.reports.sales.visitors import customers


def _sales(db: Session, start: date, end: date, outlet_id: str | None) -> Sales:
    count, voided, total, cash = repository.sales_totals(db, start, end, outlet_id)

    # Orders without a method predate the column and were cash, so they merge into the cash row here, not in GROUP BY.
    masters = repository.master_by_code(db)
    merged: dict[str, list] = {}
    for master_id, method, method_count, subtotal in repository.sales_by_method(db, start, end, outlet_id):
        code = method or CASH_METHOD
        key = master_id or masters.get(code) or f"code:{code}"
        entry = merged.setdefault(key, [code, 0, Decimal("0")])
        entry[1] += method_count
        entry[2] += Decimal(str(subtotal or 0))
    by_method = sorted(merged.values(), key=lambda entry: entry[2], reverse=True)

    return Sales(
        transaction_count=count,
        voided_count=voided,
        total=total,
        cash_total=cash,
        non_cash_total=total - cash,
        average_transaction=(total / count).quantize(RUPIAH) if count else Decimal("0"),
        by_method=[MethodSales(method=code, transaction_count=n, total=subtotal) for code, n, subtotal in by_method],
        top_items=[
            TopItem(menu_item_id=menu_item_id, name=name, qty=qty, total=Decimal(str(subtotal)))
            for menu_item_id, name, qty, subtotal in repository.top_items(db, start, end, outlet_id)
        ],
        bottom_items=[
            TopItem(menu_item_id=menu_item_id, name=name, qty=qty, total=Decimal(str(subtotal)))
            for menu_item_id, name, qty, subtotal in repository.bottom_items(db, start, end, outlet_id)
        ],
    )


def _expenses(db: Session, start: date, end: date, outlet_id: str | None) -> Expenses:
    drawer, other, count = repository.expense_totals(db, start, end, outlet_id)
    return Expenses(
        start=start,
        end=end,
        total=drawer + other,
        drawer_cash_total=drawer,
        other_funds_total=other,
        transaction_count=count,
        by_item=[
            ExpenseItem(item_name=name, routine_item_id=routine_item_id, frequency=frequency, total=Decimal(str(total)))
            for name, routine_item_id, frequency, total in repository.expense_items(db, start, end, outlet_id)
        ],
    )


def summary(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> Summary:
    """Money in, money out, and visitors of one range, so the dashboard never mixes two ranges."""
    start, end = from_today(start, end)
    sold = _sales(db, start, end, outlet_id)
    spent = _expenses(db, start, end, outlet_id)
    return Summary(
        start=start,
        end=end,
        sales=sold,
        expenses=spent,
        customers=customers(db, start, end, outlet_id),
        gross_profit=sold.total - spent.total,
    )
