"""Attendance flows: clock in, clock out, screen state, and auto-close notices."""
import uuid
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core import uploads
from app.core.clock import local_date
from app.core.errors import DomainError
from app.core.uploads import UploadedFile
from app.employee.attendance import auto_close, clock_in_block, messages, repository
from app.employee.attendance.clock_in_block import ClockInBlock
from app.employee.attendance.constants import BLOCK_NO_PERMISSION, PERMISSION_SELF_ATTENDANCE, STORED_LOCATION_MODE
from app.employee.attendance.location_validation import Location, validate_location
from app.employee.attendance.photo_store import clock_in_path, clock_out_path
from app.employee.attendance.self_schedule import service as self_schedule
from app.employee.attendance.status_rules import refresh_status
from app.employee.attendance.upload import RULE
from app.employee.schedule.lookup import around, claim_for_clock_in, offered_for_clock_in, open_for_clock_in
from app.models.attendance import Attendance, AttendanceStatus
from app.models.outlet import Outlet
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode
from app.models.user import User


@dataclass(frozen=True)
class Notice:
    record: Attendance
    code: ShiftCode | None


@dataclass(frozen=True)
class AttendanceState:
    day: date
    record: Attendance | None
    schedule: Schedule | None
    can_clock_in: bool
    can_clock_out: bool
    notices: list[Notice]
    clock_in_block: ClockInBlock | None
    can_self_schedule: bool
    branch: Outlet | None


def _note(location: Location) -> str | None:
    return (location.note or "").strip() or None


def _close_expired(db: Session, user_id: str, now: datetime) -> None:
    if auto_close.close_expired(db, user_id, now):
        db.commit()


def clock_in(
    db: Session, user: User, schedule_id: str, location: Location, photo: UploadedFile, now: datetime
) -> Attendance:
    """Clocks in to the assignment the app names, at the branch of that assignment; nothing is chosen on the employee's behalf."""
    _close_expired(db, user.id, now)

    schedule = next((item for item in open_for_clock_in(db, user.id, now) if item.id == schedule_id), None)
    if schedule is None:
        raise DomainError(messages.SCHEDULE_NOT_OPEN)
    outlet_id = schedule.outlet_id
    distance = validate_location(db, outlet_id, location)
    if repository.find_open(db, user.id) is not None:
        raise DomainError(messages.ALREADY_CLOCKED_IN)
    if not claim_for_clock_in(db, schedule.id):
        raise DomainError(messages.SCHEDULE_NOT_OPEN)

    record = repository.find_reusable(db, schedule, user.id)
    if record is None:
        record = Attendance(
            id=str(uuid.uuid4()),
            outlet_id=outlet_id,
            user_id=user.id,
            date=schedule.date,
            shift_code_id=schedule.shift_code_id,
            schedule_id=schedule.id,
        )
        db.add(record)

    record.outlet_id = outlet_id
    record.status = AttendanceStatus.PRESENT
    record.clock_in_at = now
    record.clock_out_at = None
    record.clock_in_latitude = location.latitude
    record.clock_in_longitude = location.longitude
    record.clock_in_accuracy = location.accuracy
    record.clock_in_location_mode = STORED_LOCATION_MODE[location.mode]
    record.clock_in_location_note = _note(location)
    record.clock_in_distance_meters = distance.meters
    record.clock_in_radius_meters = distance.radius
    record.clock_in_photo_path = clock_in_path(record.id, photo)
    refresh_status(db, record)
    uploads.store(db, record.clock_in_photo_path, photo, RULE)
    return record


def clock_out(db: Session, user: User, location: Location, photo: UploadedFile, now: datetime) -> Attendance:
    """Clocks out at the branch the open clock-in was made at."""
    _close_expired(db, user.id, now)

    record = repository.find_open(db, user.id)
    if record is None:
        if repository.pending_notices(db, user.id):
            raise DomainError(messages.AUTO_CLOSED)
        raise DomainError(messages.NOT_CLOCKED_IN)
    distance = validate_location(db, record.outlet_id, location)

    record.clock_out_at = now
    record.clock_out_latitude = location.latitude
    record.clock_out_longitude = location.longitude
    record.clock_out_accuracy = location.accuracy
    record.clock_out_location_mode = STORED_LOCATION_MODE[location.mode]
    record.clock_out_location_note = _note(location)
    record.clock_out_distance_meters = distance.meters
    record.clock_out_radius_meters = distance.radius
    record.clock_out_photo_path = clock_out_path(record.id, photo)
    refresh_status(db, record)
    uploads.store(db, record.clock_out_photo_path, photo, RULE)
    return record


def get_state(db: Session, user: User, now: datetime) -> AttendanceState:
    _close_expired(db, user.id, now)

    today = local_date(now)
    open_record = repository.find_open(db, user.id)
    record = open_record
    if record is None:
        last = repository.last_closed(db, user.id)
        if last is not None and local_date(last.clock_out_at) == today:
            record = last

    # Without an open clock-in, the schedule shown is the one the next clock-in will name.
    offered = None if open_record is not None else offered_for_clock_in(db, user.id, now)
    blocked = open_record is None and offered is None
    # The same branch clock_in and clock_out validate against.
    branch_id = open_record.outlet_id if open_record is not None else offered.outlet_id if offered is not None else None
    # The clock-in and clock-out routes need the permission, so a role without it is told here instead of after a photo and a position are taken.
    may_clock = user.allows(PERMISSION_SELF_ATTENDANCE)
    block = clock_in_block.find(around(db, user.id, now), now) if blocked else None
    return AttendanceState(
        day=today,
        record=record,
        schedule=repository.schedule_of(db, open_record) or offered or repository.schedule_of(db, record),
        can_clock_in=may_clock and offered is not None,
        can_clock_out=may_clock and open_record is not None,
        notices=[Notice(item, repository.code_by_id(db, item.shift_code_id)) for item in repository.pending_notices(db, user.id)],
        clock_in_block=block if may_clock else ClockInBlock(BLOCK_NO_PERMISSION, None, None),
        can_self_schedule=may_clock and blocked and self_schedule.can_make(db, user, now),
        branch=db.get(Outlet, branch_id) if branch_id else None,
    )


def acknowledge_notices(db: Session, user: User, ids: list[str]) -> None:
    """Marks only the given ids, and only when they belong to this employee."""
    for record in repository.pending_notices(db, user.id):
        if record.id in ids:
            record.notice_seen = True
