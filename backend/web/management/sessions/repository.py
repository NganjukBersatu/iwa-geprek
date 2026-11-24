"""Database reads for the cash sessions of the dashboard."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.finance.session_totals import expenses_column, revenue_column
from app.core.sorting import SqlSorting
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.expense import Expense
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.core.business_days import sessions_in


SORTING = SqlSorting(
    columns={
        "cashier": User.username,
        "opened_at": CashSession.opened_at,
        "revenue": revenue_column(CashSession.id),
        "expenses": expenses_column(CashSession.id),
        "profit": revenue_column(CashSession.id) - expenses_column(CashSession.id),
    },
    # A session still running stays on top, then the newest opened.
    default=((CashSession.status == CashSessionStatus.OPEN).desc(), CashSession.opened_at.desc()),
    tiebreak=CashSession.id,
)


def sessions_started_in(
    db: Session, start: date, end: date, outlet_id: str | None, sort: str | None, limit: int
) -> tuple[list[tuple[CashSession, str]], int]:
    """The asked order decides which sessions fill the limit; the cashier's username is joined so one page costs one query."""
    conditions = (
        *sessions_in(start, end, outlet_id),
    )
    total = db.scalar(select(func.count()).select_from(CashSession).where(*conditions)) or 0
    rows = db.execute(
        select(CashSession, User.username)
        .join(User, User.id == CashSession.cashier_id)
        .where(*conditions)
        .order_by(*SORTING.order_by(sort))
        .limit(limit)
    ).all()
    return [(session, username) for session, username in rows], total


def find(db: Session, session_id: str) -> CashSession | None:
    return db.get(CashSession, session_id)


def sold_lines(db: Session, session_id: str) -> list[tuple]:
    """One row per item sold in the session's orders that were not voided."""
    return list(
        db.execute(
            select(Order.created_at, OrderItem.menu_item_name, OrderItem.subtotal, OrderItem.qty, Order.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.cash_session_id == session_id, Order.voided_at.is_(None))
        ).all()
    )


def expense_lines(db: Session, session_id: str) -> list[tuple]:
    return list(db.execute(select(Expense.created_at, Expense.item_name, Expense.amount).where(Expense.cash_session_id == session_id)).all())
