"""Database reads of the daily overview."""
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.business_days import expenses_in, valid_orders_in
from app.models.expense import Expense, FundSource
from app.models.order import Order

CASH, OTHER = 1, 0


def order_totals(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple[date, int, Decimal]]:
    """(business day, cash or not, total) of valid orders: one grouped query, however many orders there are."""
    day = Order.business_day
    kind = case((Order.is_cash(), CASH), else_=OTHER)
    return [
        (row_day, row_kind, Decimal(str(total or 0)))
        for row_day, row_kind, total in db.execute(
            select(day, kind, func.sum(Order.total)).where(*valid_orders_in(start, end, outlet_id)).group_by(day, kind)
        ).all()
    ]


def order_totals_by_outlet(db: Session, start: date, end: date, outlet_ids: list[str]) -> list[tuple[str, date, int, Decimal]]:
    """(branch, business day, cash or not, total) of valid orders of several branches in one grouped query."""
    day = Order.business_day
    kind = case((Order.is_cash(), CASH), else_=OTHER)
    return [
        (outlet_id, row_day, row_kind, Decimal(str(total or 0)))
        for outlet_id, row_day, row_kind, total in db.execute(
            select(Order.outlet_id, day, kind, func.sum(Order.total))
            .where(*valid_orders_in(start, end, None), Order.outlet_id.in_(outlet_ids))
            .group_by(Order.outlet_id, day, kind)
        ).all()
    ]


def expense_totals_by_outlet(db: Session, start: date, end: date, outlet_ids: list[str]) -> list[tuple[str, date, int, Decimal]]:
    """(branch, business day, drawer cash or not, amount) of expenses of several branches in one grouped query."""
    day = Expense.business_day
    kind = case((Expense.fund_source == FundSource.DRAWER_CASH, CASH), else_=OTHER)
    return [
        (outlet_id, row_day, row_kind, Decimal(str(total or 0)))
        for outlet_id, row_day, row_kind, total in db.execute(
            select(Expense.outlet_id, day, kind, func.sum(Expense.amount))
            .where(*expenses_in(start, end, None), Expense.outlet_id.in_(outlet_ids))
            .group_by(Expense.outlet_id, day, kind)
        ).all()
    ]


def expense_totals(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple[date, int, Decimal]]:
    """(business day, drawer cash or not, amount) of expenses: one grouped query."""
    day = Expense.business_day
    kind = case((Expense.fund_source == FundSource.DRAWER_CASH, CASH), else_=OTHER)
    return [
        (row_day, row_kind, Decimal(str(total or 0)))
        for row_day, row_kind, total in db.execute(
            select(day, kind, func.sum(Expense.amount)).where(*expenses_in(start, end, outlet_id)).group_by(day, kind)
        ).all()
    ]
