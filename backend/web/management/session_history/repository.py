"""Database reads for the cash session history."""
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.business_days import sessions_in
from app.core.finance.session_totals import expenses_column, revenue_column
from app.core.search import contains
from app.core.sorting import SqlSorting
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.outlet import Outlet
from app.models.user import User

SORTING = SqlSorting(
    columns={
        "cashier": User.username,
        "outlet": select(Outlet.name).where(Outlet.id == CashSession.outlet_id).scalar_subquery(),
        "opened_at": CashSession.opened_at,
        "closed_at": CashSession.closed_at,
        "revenue": revenue_column(CashSession.id),
        "expenses": expenses_column(CashSession.id),
        "difference": CashSession.difference,
    },
    default=(CashSession.opened_at.desc(),),
    tiebreak=CashSession.id,
)


def page_of(
    db: Session,
    start: date,
    end: date,
    outlet_id: str | None,
    running: bool | None,
    search: str | None,
    sort: str | None,
    page: int,
    size: int,
) -> tuple[list[tuple[CashSession, str]], int]:
    filters = [
        *sessions_in(start, end, outlet_id),
    ]
    if running is not None:
        filters.append(CashSession.status == (CashSessionStatus.OPEN if running else CashSessionStatus.CLOSED))
    if search:
        filters.append(
            or_(contains(User.username, search), contains(User.name, search), contains(CashSession.shift_code, search), contains(CashSession.note, search))
        )
    joined = select(CashSession, User.username).join(User, User.id == CashSession.cashier_id).where(*filters)
    total = db.scalar(select(func.count()).select_from(joined.subquery())) or 0
    rows = db.execute(joined.order_by(*SORTING.order_by(sort)).offset((page - 1) * size).limit(size)).all()
    return [(session, username) for session, username in rows], total


def find_with_cashier(db: Session, session_id: str) -> tuple[CashSession, str] | None:
    row = db.execute(
        select(CashSession, User.username).join(User, User.id == CashSession.cashier_id).where(CashSession.id == session_id)
    ).first()
    return (row[0], row[1]) if row else None
