"""Database reads only the management web needs; the expense reads shared with the tablet live in app.core.finance.expense_reads."""
from datetime import date

from sqlalchemy import or_, select, tuple_
from sqlalchemy.orm import Session

from app.core import page_cursor
from app.core.clock import as_aware
from app.core.search import contains
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.user import User
from app.core.branches import branch_filter
from app.core.business_days import within


def session_choices(
    db: Session,
    outlet_id: str | None,
    start: date | None,
    end: date | None,
    search: str | None,
    include_closed: bool,
    size: int,
    after: page_cursor.Position | None = None,
) -> list[tuple[CashSession, str]]:
    """Sessions an expense may be attached to, newest first; closed ones only for those who may correct them."""
    filters = [*branch_filter(CashSession.outlet_id, outlet_id)]
    if after:
        filters.append(tuple_(CashSession.opened_at, CashSession.id) < tuple_(after.at, after.id))
    if not include_closed:
        filters.append(CashSession.status == CashSessionStatus.OPEN)
    if start and end:
        filters += [*within(CashSession.business_day, start, end)]
    if search:
        filters.append(or_(contains(User.username, search), contains(User.name, search), contains(CashSession.shift_code, search)))
    rows = db.execute(
        select(CashSession, User.username)
        .join(User, User.id == CashSession.cashier_id)
        .where(*filters)
        .order_by(CashSession.opened_at.desc(), CashSession.id.desc())
        .limit(size)
    ).all()
    return [(session, username) for session, username in rows]


def session_choice_page(
    db: Session, outlet_id: str | None, start: date | None, end: date | None, search: str | None, include_closed: bool, size: int, scope: str, cursor: str | None
) -> tuple[list[tuple[CashSession, str]], str | None]:
    """One page of session choices by keyset, since sessions keep growing; the cursor is bound to the filters in scope."""
    after = page_cursor.decode(scope, cursor) if cursor else None
    found = session_choices(db, outlet_id, start, end, search, include_closed, size + 1, after)
    rows = found[:size]
    next_cursor = None
    if len(found) > size:
        last = rows[-1][0]
        next_cursor = page_cursor.encode(scope, page_cursor.Position(at=as_aware(last.opened_at), id=last.id))
    return rows, next_cursor
