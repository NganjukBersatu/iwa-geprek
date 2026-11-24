"""Database reads for the mutation screen; only sessions opened with the three money parts are listed."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cash_session import CashSession
from app.models.expense import Expense
from app.models.user import User
from app.core.business_days import sessions_in


def three_part_sessions(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple[CashSession, str]]:
    """Every matching session, newest first: the range summary needs all of them, not only one page."""
    rows = db.execute(
        select(CashSession, User.username)
        .join(User, User.id == CashSession.cashier_id)
        .where(
            CashSession.planned_shopping.is_not(None),
            *sessions_in(start, end, outlet_id),
        )
        .order_by(CashSession.opened_at.desc(), CashSession.id)
    ).all()
    return [(session, username) for session, username in rows]


def find_with_cashier(db: Session, session_id: str) -> tuple[CashSession, str] | None:
    row = db.execute(
        select(CashSession, User.username).join(User, User.id == CashSession.cashier_id).where(CashSession.id == session_id)
    ).first()
    return (row[0], row[1]) if row else None


def expenses_of(db: Session, session_id: str) -> list[Expense]:
    return list(db.scalars(select(Expense).where(Expense.cash_session_id == session_id).order_by(Expense.created_at, Expense.id)).all())
