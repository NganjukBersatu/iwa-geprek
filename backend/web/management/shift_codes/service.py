"""Shift codes of a branch, owned entirely by the admin; the system only links them to the schedule board and lateness."""
import uuid

from sqlalchemy.orm import Session

from app.core import master_id, text_rules
from app.core.clock import now, today
from app.core.errors import DomainError
from app.core.messages import SHIFT_CODE_FORMAT
from app.employee.schedule.assignment import stored_window
from app.employee.schedule.window import duration_minutes
from app.models.shift_code import ShiftCode
from app.models.user import User
from web.management.shift_codes import category_rules, clock_rules, messages, repository
from web.management.shift_codes.constants import CATEGORY_KIND
from web.management.shift_codes.domain import ShiftCodeChanges, ShiftCodeDraft

NOT_FOUND = 404
CONFLICT = 409

# An empty value for these is ignored instead of clearing them.
KEPT_WHEN_EMPTY = ("category_id", "code", "is_day_off", "sort_order")
CLOCK_FIELDS = ("start_clock", "end_clock")


def list_codes(db: Session, outlet_id: str | None) -> list[ShiftCode]:
    return repository.codes(db, outlet_id)


def create(db: Session, outlet_id: str, draft: ShiftCodeDraft) -> ShiftCode:
    code = draft.code.strip()
    _ensure_code_format(code)
    _ensure_code_free(db, outlet_id, code)
    current = now()
    shift_code = ShiftCode(
        id=str(uuid.uuid4()),
        outlet_id=outlet_id,
        master_id=master_id.for_new_row(db, ShiftCode, ShiftCode.code, code, outlet_id),
        category_id=_category(db, draft.category_id),
        code=code,
        start_clock=draft.start_clock,
        end_clock=draft.end_clock,
        overtime_start_clock=draft.overtime_start_clock,
        overtime_end_clock=draft.overtime_end_clock,
        color=draft.color,
        is_day_off=draft.is_day_off,
        sort_order=draft.sort_order,
        created_at=current,
        updated_at=current,
    )
    _check(shift_code)
    _check_clocks(shift_code, draft.crosses_midnight)
    _check_category(db, shift_code)
    db.add(shift_code)
    db.commit()
    db.refresh(shift_code)
    return shift_code


def update(db: Session, user: User, code_id: str, changes: ShiftCodeChanges) -> ShiftCode:
    shift_code = _shift_code(db, user, code_id)
    values = dict(changes.values)
    if values.get("code") is not None:
        values["code"] = values["code"].strip()
        if values["code"] != shift_code.code:
            _ensure_code_format(values["code"])
        _ensure_code_free(db, shift_code.outlet_id, values["code"], except_id=shift_code.id)
    if values.get("category_id") is not None:
        values["category_id"] = _category(db, values["category_id"])
    old_clocks = (shift_code.start_clock, shift_code.end_clock)
    old_matching = (shift_code.category_id, shift_code.start_clock, shift_code.is_day_off)
    old_shape = (shift_code.start_clock, shift_code.end_clock, shift_code.is_day_off)
    for field, value in values.items():
        if field in KEPT_WHEN_EMPTY and value is None:
            continue
        setattr(shift_code, field, value)
    _check(shift_code)
    # Hanya saat jam atau status libur berubah, supaya kode lama yang jamnya sudah tidak wajar tetap bisa diubah warnanya.
    if (shift_code.start_clock, shift_code.end_clock, shift_code.is_day_off) != old_shape:
        _check_clocks(shift_code, bool(changes.crosses_midnight))
    # Hanya saat kategori, jam mulai, atau status libur berubah, supaya kode lama yang sudah tidak cocok tetap bisa diubah warnanya.
    if (shift_code.category_id, shift_code.start_clock, shift_code.is_day_off) != old_matching:
        _check_category(db, shift_code)
    shift_code.updated_at = now()
    if (shift_code.start_clock, shift_code.end_clock) != old_clocks:
        _refresh_upcoming_windows(db, shift_code)
    # A code that became a day off must not stay on work schedules, and the other way round.
    if shift_code.is_day_off:
        repository.detach_from_schedules(db, shift_code.id)
    else:
        repository.detach_from_days_off(db, shift_code.id)
    db.commit()
    db.refresh(shift_code)
    return shift_code


def delete(db: Session, user: User, code_id: str) -> None:
    """Schedules using the code stay and only lose it, through the database's SET NULL."""
    db.delete(_shift_code(db, user, code_id))
    db.commit()


def _shift_code(db: Session, user: User, code_id: str) -> ShiftCode:
    shift_code = repository.find(db, code_id)
    locked = user.locked_outlet_id
    if shift_code is None or (locked and shift_code.outlet_id != locked):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return shift_code


def _ensure_code_format(code: str) -> None:
    if not text_rules.is_shift_code(code):
        raise DomainError(SHIFT_CODE_FORMAT, field="code")


def _ensure_code_free(db: Session, outlet_id: str, code: str, except_id: str | None = None) -> None:
    owner = repository.code_owner(db, outlet_id, code)
    if owner is not None and owner.id != except_id:
        raise DomainError(messages.CODE_TAKEN.format(code=code), status=CONFLICT, field="code")


def _category(db: Session, category_id: str | None) -> str | None:
    if not category_id:
        return None
    if not repository.category_exists(db, CATEGORY_KIND, category_id):
        raise DomainError(messages.CATEGORY_NOT_FOUND, field="category")
    return category_id


def _check(shift_code: ShiftCode) -> None:
    """A work code needs start and end clocks and paired overtime clocks; a day-off code carries none; the duration follows the clocks."""
    if shift_code.is_day_off:
        shift_code.start_clock = shift_code.end_clock = None
        shift_code.overtime_start_clock = shift_code.overtime_end_clock = None
    else:
        if not shift_code.start_clock or not shift_code.end_clock:
            raise DomainError(messages.WORK_CLOCKS_REQUIRED, field="start_clock")
        if bool(shift_code.overtime_start_clock) != bool(shift_code.overtime_end_clock):
            raise DomainError(messages.OVERTIME_UNPAIRED, field="overtime_start_clock")
        if not shift_code.overtime_start_clock:
            shift_code.overtime_start_clock = shift_code.overtime_end_clock = None
    shift_code.duration_minutes = duration_minutes(shift_code.start_clock, shift_code.end_clock)


def _check_clocks(shift_code: ShiftCode, crosses_midnight: bool) -> None:
    if not shift_code.is_day_off and shift_code.start_clock and shift_code.end_clock:
        clock_rules.ensure_valid(shift_code.start_clock, shift_code.end_clock, crosses_midnight=crosses_midnight)


def _check_category(db: Session, shift_code: ShiftCode) -> None:
    category = repository.category_by_id(db, shift_code.category_id) if shift_code.category_id else None
    if category is not None:
        category_rules.ensure_matches(category, is_day_off=shift_code.is_day_off, start_clock=shift_code.start_clock)


def _refresh_upcoming_windows(db: Session, shift_code: ShiftCode) -> None:
    """Schedules from today on follow the new clocks; past ones keep the window they were worked under."""
    for schedule in repository.upcoming_schedules(db, shift_code.id, today()):
        schedule.starts_at, schedule.ends_at = stored_window(schedule.date, shift_code)
