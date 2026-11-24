"""Days off on the board, kept apart from assignments because a day off has no working session."""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.employee.schedule import rules
from app.models.day_off import DayOff
from web.management.schedule.days_off import messages, repository
from web.management.schedule.days_off.domain import DayOffDraft

NOT_FOUND = 404
FORBIDDEN = 403
CONFLICT = 409


def list_days_off(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> list[DayOff]:
    first, last = rules.week_range(start, end)
    return repository.in_range(db, first, last, outlet_id)


def create(db: Session, locked_outlet_id: str | None, draft: DayOffDraft) -> DayOff:
    """The day off belongs to the branch the person is placed at."""
    user = rules.active_user(db, draft.user_id)
    if locked_outlet_id and user.outlet_id != locked_outlet_id:
        raise DomainError(messages.OTHER_BRANCH, status=FORBIDDEN)
    if not user.outlet_id:
        raise DomainError(messages.NO_BRANCH.format(username=user.username))
    if repository.scheduled_on(db, draft.date, user.id):
        raise DomainError(messages.STILL_SCHEDULED, status=CONFLICT)
    if repository.off_on(db, draft.date, user.id):
        raise DomainError(messages.ALREADY_OFF, status=CONFLICT)
    if draft.shift_code_id:
        code = repository.find_code(db, draft.shift_code_id)
        if code is None or code.outlet_id != user.outlet_id or not code.is_day_off:
            raise DomainError(messages.NOT_DAY_OFF_CODE)
    day_off = DayOff(
        id=str(uuid.uuid4()),
        outlet_id=user.outlet_id,
        date=draft.date,
        user_id=user.id,
        shift_code_id=draft.shift_code_id,
        note=(draft.note or "").strip() or None,
    )
    db.add(day_off)
    db.commit()
    db.refresh(day_off)
    return day_off


def delete(db: Session, locked_outlet_id: str | None, day_off_id: str) -> None:
    day_off = repository.find(db, day_off_id)
    # Another branch's day off answers as missing for someone bound to one branch.
    if day_off is None or (locked_outlet_id and day_off.outlet_id != locked_outlet_id):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    db.delete(day_off)
    db.commit()
