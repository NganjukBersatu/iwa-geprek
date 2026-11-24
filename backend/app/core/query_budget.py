"""The time budget of every database statement: the database cancels what runs past the limit, and slow ones are logged before they get there.

The limit holds for every query, heavy or small, and it is the owner's standard: a statement that needs more than this is rewritten, not given more time.
"""
import logging
import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError

from app.core import request_timing

QUERY_LIMIT_MILLISECONDS = 1000
SLOW_QUERY_MILLISECONDS = 500
CANCELLED_STATE = "57014"
STATEMENT_LOG_CHARACTERS = 300
MILLISECONDS_PER_SECOND = 1000

log = logging.getLogger("cafe.query")


def install(engine: Engine) -> None:
    if engine.dialect.name == "postgresql":
        event.listen(engine, "connect", _limit_statements)
    event.listen(engine, "before_cursor_execute", _start)
    event.listen(engine, "after_cursor_execute", _finish)


def _limit_statements(dbapi_connection: Any, _record: Any) -> None:
    """Session level, and committed: a setting made inside a transaction that is rolled back would be undone with it."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute(f"SET statement_timeout = {QUERY_LIMIT_MILLISECONDS}")
    finally:
        cursor.close()
    dbapi_connection.commit()


def _start(_connection: Any, _cursor: Any, _statement: str, _parameters: Any, context: Any, _executemany: bool) -> None:
    context.query_started = time.perf_counter()


def _finish(_connection: Any, _cursor: Any, statement: str, _parameters: Any, context: Any, _executemany: bool) -> None:
    elapsed = (time.perf_counter() - context.query_started) * MILLISECONDS_PER_SECOND
    request_timing.statement_ran(elapsed)
    if elapsed >= SLOW_QUERY_MILLISECONDS:
        log.warning("slow query, %.0f ms (limit %d): %s", elapsed, QUERY_LIMIT_MILLISECONDS, " ".join(statement.split())[:STATEMENT_LOG_CHARACTERS])


def was_cancelled(error: BaseException) -> bool:
    """Whether the database cancelled the statement for running past the limit."""
    if not isinstance(error, DBAPIError):
        return False
    state = getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)
    return state == CANCELLED_STATE
