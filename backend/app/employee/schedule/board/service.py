"""Reads the schedule of a branch for one month."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.branches import outlet_name
from app.core.period import month_bounds
from app.employee.schedule.board import repository
from app.employee.schedule.board.domain import MonthBoard
from app.models.schedule import Schedule


def month_board(db: Session, outlet_id: str | None, month_start: date) -> MonthBoard:
    """An account bound to a branch sees that branch only, including the colleagues on shift."""
    first, last = month_bounds(month_start)
    return MonthBoard(
        month_start=first,
        outlet_name=outlet_name(db, outlet_id),
        assignments=repository.assignments_between(db, first, last, outlet_id),
        days_off=repository.days_off_between(db, first, last, outlet_id),
        shift_codes=repository.shift_codes(db, outlet_id),
    )


def my_assignments(db: Session, user_id: str, day: date) -> list[Schedule]:
    return repository.assignments_of(db, user_id, day)
