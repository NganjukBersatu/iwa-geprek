"""An open bill stays out of every read of orders, so reports and session totals never count money that has not been paid.

A route that must see bills (the stations and the history list) says so once on its router; the code that works on a bill asks per statement.
"""
from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria

from app.core.database import get_db
from app.models.order import Order

INCLUDE_OPTION = "include_open_bills"
SESSION_FLAG = "show_open_bills"


def _hide_open_bills(state: ORMExecuteState) -> None:
    if not (state.is_select or state.is_update or state.is_delete):
        return
    if state.is_column_load or state.is_relationship_load:
        return
    if state.execution_options.get(INCLUDE_OPTION) or state.session.info.get(SESSION_FLAG):
        return
    state.statement = state.statement.options(with_loader_criteria(Order, Order.is_open.is_(False), include_aliases=True))


def watch_open_bills() -> None:
    """Called at startup; a second call adds nothing."""
    if event.contains(Session, "do_orm_execute", _hide_open_bills):
        return
    event.listen(Session, "do_orm_execute", _hide_open_bills)


def show_open_bills(db: Session = Depends(get_db)) -> None:
    """Router dependency: every read of this request sees open bills as well."""
    db.info[SESSION_FLAG] = True
