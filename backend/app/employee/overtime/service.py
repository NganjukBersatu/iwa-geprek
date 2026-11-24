"""Recording unplanned overtime, and reading everything a person has counted."""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.clock import as_aware, local_date
from app.core.errors import DomainError
from app.core.period import month_bounds
from app.employee.overtime import ledger, messages, repository
from app.models.overtime import Overtime
from app.models.user import User

CONFLICT = 409
UNPROCESSABLE = 422


def record_unplanned(db: Session, user: User, start_at: datetime, end_at: datetime, note: str) -> Overtime:
    """Allowed only on a day without scheduled overtime, because that one is already counted by the schedule."""
    if not user.working_outlet_id:
        raise DomainError(messages.NO_BRANCH)
    start_at, end_at, note = as_aware(start_at), as_aware(end_at), note.strip()
    if end_at <= start_at:
        raise DomainError(messages.END_BEFORE_START, status=UNPROCESSABLE)
    if not note:
        raise DomainError(messages.NOTE_REQUIRED, status=UNPROCESSABLE)

    repository.lock_user(db, user.id)
    day = local_date(start_at)
    if ledger.scheduled_on(db, user.id, day) is not None:
        raise DomainError(messages.SCHEDULED_EXISTS, status=CONFLICT)
    if repository.overlaps(db, user.id, start_at, end_at):
        raise DomainError(messages.OVERLAPS, status=CONFLICT)

    item = Overtime(outlet_id=user.working_outlet_id, user_id=user.id, date=day, start_at=start_at, end_at=end_at, note=note)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def history(db: Session, user: User, month_start: date) -> list[ledger.Entry]:
    first, last = month_bounds(month_start)
    return ledger.month_entries(db, user.id, first, last)
