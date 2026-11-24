"""Assignments on the schedule board: who works which code on which day, arranged by people holding jadwal.kelola."""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.clock import now
from app.core.errors import DomainError
from app.employee.schedule import rules
from app.employee.schedule.assignment import stored_window
from app.models.schedule import Schedule
from web.management.schedule.assignments import messages, repository
from web.management.schedule.assignments.domain import AssignmentChanges, AssignmentDraft

NOT_FOUND = 404
CONFLICT = 409


def list_assignments(
    db: Session, start: date | None, end: date | None, outlet_id: str | None, user_id: str | None, sort: str | None
) -> list[Schedule]:
    first, last = rules.week_range(start, end)
    return repository.in_range(db, first, last, outlet_id, user_id, sort)


def get(db: Session, outlet_id: str | None, schedule_id: str) -> Schedule:
    """One assignment; another branch's answers as missing, so its existence is not revealed."""
    return _schedule(db, schedule_id, outlet_id)


def create(db: Session, outlet_id: str, draft: AssignmentDraft) -> Schedule:
    """The branch is the one being managed, not the person's own placement, so someone can be lent to another branch."""
    rules.active_user(db, draft.user_id)
    if not draft.shift_code_id:
        raise DomainError(messages.CODE_REQUIRED)
    _ensure_work_code(db, draft.shift_code_id, outlet_id)
    _ensure_free_slot(db, draft.date, draft.shift_code_id, draft.user_id)
    rules.ensure_not_day_off(db, draft.date, draft.user_id)
    _ensure_role(db, draft.role_id)
    current = now()
    schedule = Schedule(
        id=str(uuid.uuid4()),
        outlet_id=outlet_id,
        date=draft.date,
        user_id=draft.user_id,
        note=_note(draft.note),
        role_id=draft.role_id,
        shift_code_id=draft.shift_code_id,
        created_at=current,
        updated_at=current,
    )
    _apply_window(db, schedule)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update(db: Session, locked_outlet_id: str | None, schedule_id: str, changes: AssignmentChanges) -> Schedule:
    schedule = _schedule(db, schedule_id, locked_outlet_id)
    values = changes.values
    day = values.get("date") or schedule.date
    code_id = values["shift_code_id"] if "shift_code_id" in values else schedule.shift_code_id
    user_id = values.get("user_id") or schedule.user_id
    if user_id != schedule.user_id:
        rules.active_user(db, user_id)
    _ensure_free_slot(db, day, code_id, user_id, except_id=schedule.id)
    if day != schedule.date or user_id != schedule.user_id:
        rules.ensure_not_day_off(db, day, user_id)
    if "shift_code_id" in values:
        _ensure_work_code(db, values["shift_code_id"], schedule.outlet_id)
        schedule.shift_code_id = values["shift_code_id"]
    if "role_id" in values:
        _ensure_role(db, values["role_id"])
        schedule.role_id = values["role_id"]
    schedule.date = day
    schedule.user_id = user_id
    if "note" in values:
        schedule.note = _note(values["note"])
    schedule.updated_at = now()
    _apply_window(db, schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def delete(db: Session, locked_outlet_id: str | None, schedule_id: str) -> None:
    db.delete(_schedule(db, schedule_id, locked_outlet_id))
    db.commit()


def swap(db: Session, locked_outlet_id: str | None, first_id: str, second_id: str) -> tuple[Schedule, Schedule]:
    """The people trade places while each slot keeps its date and code, so no slot is ever empty midway."""
    if first_id == second_id:
        raise DomainError(messages.SWAP_SAME_SCHEDULE)
    first = _schedule(db, first_id, locked_outlet_id)
    second = _schedule(db, second_id, locked_outlet_id)
    if first.user_id == second.user_id:
        raise DomainError(messages.SWAP_SAME_PERSON)
    _ensure_free_slot(db, first.date, first.shift_code_id, second.user_id, except_id=first.id)
    _ensure_free_slot(db, second.date, second.shift_code_id, first.user_id, except_id=second.id)
    rules.ensure_not_day_off(db, first.date, second.user_id)
    rules.ensure_not_day_off(db, second.date, first.user_id)

    first_name, second_name = first.user.username, second.user.username
    first.user_id, second.user_id = second.user_id, first.user_id
    # The note tells whoever reads the board later why the name differs from the one arranged.
    first.note = messages.SWAP_NOTE.format(incoming=second_name, outgoing=first_name)
    second.note = messages.SWAP_NOTE.format(incoming=first_name, outgoing=second_name)
    current = now()
    for schedule in (first, second):
        schedule.updated_at = current
        _apply_window(db, schedule)
    db.commit()
    db.refresh(first)
    db.refresh(second)
    return first, second


def _schedule(db: Session, schedule_id: str, locked_outlet_id: str | None) -> Schedule:
    schedule = repository.find(db, schedule_id)
    # Another branch's assignment answers as missing for someone bound to one branch.
    if schedule is None or (locked_outlet_id and schedule.outlet_id != locked_outlet_id):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return schedule


def _ensure_work_code(db: Session, code_id: str | None, outlet_id: str) -> None:
    if not code_id:
        return
    code = repository.find_code(db, code_id)
    if code is None or code.outlet_id != outlet_id:
        raise DomainError(messages.CODE_NOT_IN_BRANCH, status=NOT_FOUND)
    if code.is_day_off:
        raise DomainError(messages.CODE_IS_DAY_OFF.format(code=code.code))


def _ensure_free_slot(db: Session, day: date, code_id: str | None, user_id: str, except_id: str | None = None) -> None:
    """One person holds a code once per day; checked here so the screen gets a reason instead of a constraint error."""
    taken = repository.same_slot(db, day, code_id, user_id)
    if taken is not None and taken.id != except_id:
        raise DomainError(messages.DUPLICATE, status=CONFLICT)


def _ensure_role(db: Session, role_id: str | None) -> None:
    """The role is only the day's label on the board, so it is checked to exist and nothing more."""
    if role_id is not None and not repository.role_exists(db, role_id):
        raise DomainError(messages.ROLE_NOT_FOUND, status=NOT_FOUND)


def _apply_window(db: Session, schedule: Schedule) -> None:
    code = repository.find_code(db, schedule.shift_code_id) if schedule.shift_code_id else None
    schedule.starts_at, schedule.ends_at = stored_window(schedule.date, code)


def _note(text: str | None) -> str | None:
    return (text or "").strip() or None
