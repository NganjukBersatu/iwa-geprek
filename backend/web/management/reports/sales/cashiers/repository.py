"""Database reads of the cashier report, one aggregate per source so joins cannot multiply sums."""
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.business_days import expenses_in, orders_in, sessions_in, valid_orders_in
from app.core.money import decimal_of
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.expense import Expense
from app.models.order import Order


def sales_by_cashier(
    db: Session, start: date, end: date, outlet_id: str | None
) -> dict[str, tuple[int, Decimal, Decimal]]:
    return {
        cashier_id: (count, decimal_of(total), decimal_of(cash))
        for cashier_id, count, total, cash in db.execute(
            select(
                Order.cashier_id,
                func.count(),
                func.sum(Order.total),
                func.sum(case((Order.is_cash(), Order.total), else_=0)),
            )
            .where(*valid_orders_in(start, end, outlet_id))
            .group_by(Order.cashier_id)
        ).all()
    }


def voids_by_cashier(db: Session, start: date, end: date, outlet_id: str | None) -> dict[str, int]:
    return dict(
        db.execute(
            select(Order.cashier_id, func.count())
            .where(*orders_in(start, end, outlet_id), Order.voided_at.is_not(None))
            .group_by(Order.cashier_id)
        ).all()
    )


def expenses_by_cashier(db: Session, start: date, end: date, outlet_id: str | None) -> dict[str, Decimal]:
    """Spending in a session is its cashier's, whoever entered it; only spending outside a session is the recorder's."""
    owner = func.coalesce(CashSession.cashier_id, Expense.cashier_id)
    return {
        cashier_id: decimal_of(total)
        for cashier_id, total in db.execute(
            select(owner, func.sum(Expense.amount))
            .outerjoin(CashSession, CashSession.id == Expense.cash_session_id)
            .where(*expenses_in(start, end, outlet_id))
            .group_by(owner)
        ).all()
    }


def closed_sessions_by_cashier(db: Session, start: date, end: date, outlet_id: str | None) -> dict[str, tuple[int, Decimal]]:
    return {
        cashier_id: (count, decimal_of(difference))
        for cashier_id, count, difference in db.execute(
            select(CashSession.cashier_id, func.count(), func.sum(CashSession.difference))
            .where(CashSession.status == CashSessionStatus.CLOSED, *sessions_in(start, end, outlet_id))
            .group_by(CashSession.cashier_id)
        ).all()
    }
