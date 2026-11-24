"""The admin's view and corrections of attendance; hadir or telat is always decided by the clock, never by the button pressed."""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.clock import as_aware, now, today
from app.core.errors import DomainError
from app.employee.attendance.lateness import minutes_late
from app.employee.attendance.policy import BranchPolicy
from app.employee.attendance.status_rules import refresh_status
from app.employee.attendance.work_time import worked_minutes
from app.employee.schedule.assignment import work_window
from app.models.attendance import PRESENT_STATUSES, Attendance
from app.models.user import User
from web.management.attendance import messages, repository
from web.management.attendance.constants import DAYS_IN_WEEK, MAX_RANGE_DAYS, NOT_FOUND
from web.management.attendance.domain import AttendanceChanges, AttendanceEntry, AttendanceFilter, AttendancePage, MarkDraft


def list_page(db: Session, filter: AttendanceFilter, sort: str | None, page: int, size: int) -> AttendancePage:
    """Only reads. A clock-in left open too long is closed when that employee next opens the app (app/employee/attendance/service.py), never from here."""
    rows, total = repository.page_of(db, filter, sort, page, size)
    return AttendancePage(entries=_entries(db, rows), total=total, page=page, size=size)


def list_range(db: Session, filter: AttendanceFilter) -> list[AttendanceEntry]:
    start, end = _week_or_range(filter.start, filter.end)
    return _entries(db, repository.range_of(db, _with_range(filter, start, end)))


def mark(db: Session, admin: User, draft: MarkDraft) -> AttendanceEntry:
    """One person on one shift of one day: marking again updates the same record instead of piling up copies."""
    user = repository.find_user(db, draft.user_id)
    locked = admin.locked_outlet_id
    if user is None or (locked and user.outlet_id != locked):
        raise DomainError(messages.USER_NOT_FOUND, status=NOT_FOUND)
    if not user.outlet_id:
        raise DomainError(messages.NO_BRANCH.format(username=user.username))

    record = repository.find_slot(db, draft.date, draft.shift_code_id, draft.user_id)
    if record is None:
        record = Attendance(outlet_id=user.outlet_id, user_id=draft.user_id, date=draft.date, shift_code_id=draft.shift_code_id)
        db.add(record)
    elif draft.status not in PRESENT_STATUSES and record.clock_in_at is not None:
        raise DomainError(messages.LEAVE_KEEPS_CLOCK_IN.format(username=user.username))

    record.status = draft.status
    if draft.schedule_id is not None:
        record.schedule_id = draft.schedule_id
    elif record.schedule_id is None:
        # Linking to the plan lets the recap tell "present as scheduled" from "came without being scheduled".
        record.schedule_id = repository.find_schedule_id(db, draft.user_id, draft.date, draft.shift_code_id)
    if draft.note is not None:
        record.note = draft.note.strip() or None

    if draft.clock_in_at is not None:
        record.clock_in_at = draft.clock_in_at
    elif draft.status in PRESENT_STATUSES and record.clock_in_at is None:
        record.clock_in_at = now()
    if draft.status not in PRESENT_STATUSES:
        record.clock_in_at = None
        record.clock_out_at = None
    if draft.clock_out_at is not None:
        record.clock_out_at = draft.clock_out_at
    _check_clocks(record)
    refresh_status(db, record)
    db.commit()
    return _entry_of(db, record.id)


def get(db: Session, admin: User, record_id: str) -> AttendanceEntry:
    """One record for its page; another branch's record answers as missing."""
    _owned(db, admin, record_id)
    return _entry_of(db, record_id)


def edit(db: Session, admin: User, record_id: str, changes: AttendanceChanges) -> AttendanceEntry:
    record = _owned(db, admin, record_id)
    if changes.status is not None:
        if changes.status not in PRESENT_STATUSES and record.clock_in_at is not None:
            raise DomainError(messages.LEAVE_KEEPS_CLOCK_IN.format(username=_username(db, record)))
        record.status = changes.status
        if changes.status not in PRESENT_STATUSES:
            record.clock_in_at = None
            record.clock_out_at = None
        elif record.clock_in_at is None:
            record.clock_in_at = now()
    if "clock_in_at" in changes.given:
        record.clock_in_at = changes.clock_in_at
    if "clock_out_at" in changes.given:
        record.clock_out_at = changes.clock_out_at
    if "note" in changes.given:
        record.note = (changes.note or "").strip() or None

    if record.status in PRESENT_STATUSES and record.clock_in_at is None:
        raise DomainError(messages.PRESENT_NEEDS_CLOCK_IN)
    _check_clocks(record)
    refresh_status(db, record)
    db.commit()
    return _entry_of(db, record.id)


def delete(db: Session, admin: User, record_id: str) -> None:
    record = _owned(db, admin, record_id)
    # Kejadian pengiriman milik absen ini ikut dihapus dalam transaksi yang sama, karena absen yang dirujuknya tidak ada lagi.
    repository.delete_events(db, record.id)
    db.delete(record)
    db.commit()


def _owned(db: Session, admin: User, record_id: str) -> Attendance:
    """A branch-bound admin never reaches another branch's record, even by its id."""
    found = repository.find(db, record_id)
    locked = admin.locked_outlet_id
    if found is None or (locked and found[0].outlet_id != locked):
        raise DomainError(messages.RECORD_NOT_FOUND, status=NOT_FOUND)
    return found[0]


def _username(db: Session, record: Attendance) -> str:
    user = repository.find_user(db, record.user_id)
    return user.username if user else record.user_id


def _check_clocks(record: Attendance) -> None:
    if record.clock_in_at is None or record.clock_out_at is None:
        return
    if as_aware(record.clock_out_at) < as_aware(record.clock_in_at):
        raise DomainError(messages.CLOCK_OUT_BEFORE_IN)


def _week_or_range(start: date | None, end: date | None) -> tuple[date, date]:
    """The week of [end] (or of today) unless a range is given; two months at most."""
    if start is None:
        anchor = end or today()
        start = anchor - timedelta(days=anchor.weekday())
    if end is None:
        end = start + timedelta(days=DAYS_IN_WEEK - 1)
    if end < start:
        raise DomainError(messages.RANGE_BACKWARDS)
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise DomainError(messages.RANGE_TOO_LONG)
    return start, end


def _with_range(filter: AttendanceFilter, start: date, end: date) -> AttendanceFilter:
    return AttendanceFilter(
        start=start, end=end, user_id=filter.user_id, status=filter.status, has_photo=filter.has_photo,
        outside_schedule=filter.outside_schedule, search=filter.search, outlet_id=filter.outlet_id,
    )


def _entry_of(db: Session, record_id: str) -> AttendanceEntry:
    found = repository.find(db, record_id)
    return _entries(db, [found])[0]


def _entries(db: Session, rows: list[tuple[Attendance, User]]) -> list[AttendanceEntry]:
    schedules = repository.schedules_by_id(db, (record.schedule_id for record, _ in rows))
    codes = repository.codes_by_id(
        db,
        [record.shift_code_id for record, _ in rows] + [schedule.shift_code_id for schedule in schedules.values()],
    )
    outlets = repository.outlets_by_id(db, {record.outlet_id for record, _ in rows})
    events = repository.events_by_attendance(db, (record.id for record, _ in rows))
    policies: dict[str, BranchPolicy] = {}
    entries = []
    for record, user in rows:
        schedule = schedules.get(record.schedule_id) if record.schedule_id else None
        code = codes.get(record.shift_code_id) if record.shift_code_id else None
        if code is None and schedule is not None and schedule.shift_code_id:
            code = codes.get(schedule.shift_code_id)
        late = penalty = 0
        worked: int | None = None
        if record.status in PRESENT_STATUSES and record.clock_in_at is not None:
            window = work_window(record.date, schedule, code)
            if window is not None:
                policy = policies.setdefault(record.outlet_id, BranchPolicy.load(db, record.outlet_id))
                late = minutes_late(record.clock_in_at, window[0])
                penalty = policy.penalty(late)
            worked = worked_minutes(record, window)
        outlet = outlets.get(record.outlet_id)
        entries.append(
            AttendanceEntry(
                record=record,
                user=user,
                shift_code=code.code if code else None,
                shift_code_color=code.color if code else None,
                branch_latitude=outlet.latitude if outlet else None,
                branch_longitude=outlet.longitude if outlet else None,
                late_minutes=late,
                penalty=penalty,
                work_minutes=worked,
                events=tuple(events.get(record.id, ())),
            )
        )
    return entries
