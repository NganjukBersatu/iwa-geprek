"""Database reads for the sessions of the person holding the tablet."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.cash_session import CashSession
from app.models.user import User


def own_page(db: Session, user_id: str, start: date | None, end: date | None, page: int, size: int, sort: str | None = None) -> tuple[list[tuple[CashSession, str]], int]:
    """Newest first; a missing bound leaves that side open."""
    filters = [CashSession.cashier_id == user_id]
    if start is not None:
        filters.append(CashSession.business_day >= start)
    if end is not None:
        filters.append(CashSession.business_day <= end)
    total = db.scalar(select(func.count()).select_from(CashSession).where(*filters)) or 0
    rows = db.execute(
        select(CashSession, User.username)
        .join(User, User.id == CashSession.cashier_id)
        .where(*filters)
        .order_by(CashSession.opened_at.asc() if sort == "time" else CashSession.opened_at.desc(), CashSession.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [(session, username) for session, username in rows], total
