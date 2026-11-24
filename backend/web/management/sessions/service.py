"""Cash sessions with their money figures, and the lines of one session."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.finance.session_totals import totals_for
from web.management.reports.common import ensure_max_range, resolve_range
from web.management.sessions import messages, repository
from web.management.sessions.schemas import SessionLineOut, SessionLinesOut, SessionListOut, SessionRowOut

NOT_FOUND = 404


def sessions(db: Session, start: date | None, end: date | None, outlet_id: str | None, sort: str | None, limit: int) -> SessionListOut:
    start, end = resolve_range(start, end)
    ensure_max_range(start, end)
    found, total = repository.sessions_started_in(db, start, end, outlet_id, sort, limit)
    totals = totals_for(db, [session.id for session, _ in found])
    items = [
        SessionRowOut(
            id=session.id,
            cashier_username=username,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            revenue=totals[session.id].revenue,
            expense=totals[session.id].expenses,
        )
        for session, username in found
    ]
    return SessionListOut(start=start, end=end, total=total, items=items)


def lines(db: Session, session_id: str, outlet_id: str | None) -> SessionLinesOut:
    session = repository.find(db, session_id)
    if session is None or (outlet_id is not None and session.outlet_id != outlet_id):
        raise DomainError(messages.NOT_FOUND, NOT_FOUND)
    income = [
        SessionLineOut(at=at, kind="income", description=name, amount=amount, quantity=qty, order_id=order_id)
        for at, name, amount, qty, order_id in repository.sold_lines(db, session_id)
    ]
    outgoing = [
        SessionLineOut(at=at, kind="expense", description=name, amount=amount, quantity=None, order_id=None)
        for at, name, amount in repository.expense_lines(db, session_id)
    ]
    return SessionLinesOut(session_id=session_id, lines=sorted([*income, *outgoing], key=lambda line: line.at))
