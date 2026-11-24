"""HTTP surface of the cash sessions listed on the dashboard."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.models.user import User
from web.management.reports.common import as_http
from web.management.sessions import service
from web.management.sessions.schemas import SessionLinesOut, SessionListOut
from web.management.reports import gates

router = APIRouter(prefix="/sessions", tags=["web-sessions"])

SESSIONS = TypeAdapter(SessionListOut)
LINES = TypeAdapter(SessionLinesOut)

DEFAULT_LIMIT = 40
MAX_LIMIT = 100


@router.get("", response_model=SessionListOut)
def list_sessions(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.TRANSACTIONS)),
):
    """Cash sessions that started in the range, running ones then the newest first unless another order is asked."""
    try:
        return cache.read(
            "web.sessions",
            (start, end, outlet_id, sort, limit),
            lambda: service.sessions(db, start, end, outlet_id, sort, limit),
            SESSIONS,
            cache.LIST_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error


@router.get("/{session_id}/lines", response_model=SessionLinesOut)
def session_lines(
    session_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.TRANSACTIONS)),
):
    """What one session sold and spent, oldest first."""
    try:
        return cache.read("web.sessions.lines", (session_id, outlet_id), lambda: service.lines(db, session_id, outlet_id), LINES, cache.LIST_SECONDS)
    except DomainError as error:
        raise as_http(error) from error
