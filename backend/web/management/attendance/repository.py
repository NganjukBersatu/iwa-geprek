"""Database reads for the admin's attendance screens."""
from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.clock import now
from app.core.date_range import range_end, range_start
from app.core.search import contains
from app.models.attendance import Attendance
from app.models.attendance_clock_event import AttendanceClockEvent
from app.models.outlet import Outlet
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode
from app.models.user import User
from web.management.attendance.domain import AttendanceFilter
from app.core.sorting import SqlSorting


def _conditions(filter: AttendanceFilter) -> list:
    conditions = []
    clocked = any(getattr(bound, "clock", None) is not None for bound in (filter.start, filter.end))
    if clocked:
        # Records without a clock-in (leave, sick, absent) have no time of their own, so a time range leaves them out.
        conditions.append(Attendance.clock_in_at.is_not(None))
        if filter.end:
            conditions.append(Attendance.clock_in_at < range_end(filter.end))
        if filter.start:
            conditions.append(func.coalesce(Attendance.clock_out_at, now()) > range_start(filter.start))
    else:
        if filter.start:
            conditions.append(Attendance.date >= filter.start)
        if filter.end:
            conditions.append(Attendance.date <= filter.end)
    if filter.user_id:
        conditions.append(Attendance.user_id == filter.user_id)
    if filter.status:
        conditions.append(Attendance.status == filter.status)
    if filter.has_photo is not None:
        photo = Attendance.clock_in_photo_path
        conditions.append(photo.is_not(None) if filter.has_photo else photo.is_(None))
    if filter.outside_schedule is not None:
        reason = Attendance.outside_schedule_reason
        conditions.append(reason.is_not(None) if filter.outside_schedule else reason.is_(None))
    if filter.search:
        conditions.append(or_(contains(User.username, filter.search), contains(User.name, filter.search)))
    if filter.outlet_id:
        conditions.append(Attendance.outlet_id == filter.outlet_id)
    return conditions


SORTING = SqlSorting(
    columns={
        "name": func.coalesce(func.nullif(User.name, ""), User.username),
        "date": Attendance.date,
        "code": select(ShiftCode.code).where(ShiftCode.id == Attendance.shift_code_id).scalar_subquery(),
        "clock_in": Attendance.clock_in_at,
        "clock_out": Attendance.clock_out_at,
        "status": Attendance.status,
    },
    default=(Attendance.date.desc(), Attendance.created_at.desc()),
    tiebreak=Attendance.id,
)


def page_of(db: Session, filter: AttendanceFilter, sort: str | None, page: int, size: int) -> tuple[list[tuple[Attendance, User]], int]:
    conditions = _conditions(filter)
    total = db.scalar(select(func.count()).select_from(Attendance).join(User, Attendance.user_id == User.id).where(*conditions)) or 0
    rows = db.execute(
        select(Attendance, User)
        .join(User, Attendance.user_id == User.id)
        .where(*conditions)
        .order_by(*SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [(record, user) for record, user in rows], total


def range_of(db: Session, filter: AttendanceFilter) -> list[tuple[Attendance, User]]:
    rows = db.execute(
        select(Attendance, User)
        .join(User, Attendance.user_id == User.id)
        .where(*_conditions(filter))
        .order_by(Attendance.date, Attendance.created_at)
    ).all()
    return [(record, user) for record, user in rows]


def find(db: Session, record_id: str) -> tuple[Attendance, User] | None:
    row = db.execute(select(Attendance, User).join(User, Attendance.user_id == User.id).where(Attendance.id == record_id)).first()
    return (row[0], row[1]) if row else None


def events_by_attendance(db: Session, ids: Iterable[str]) -> dict[str, list[AttendanceClockEvent]]:
    """Kejadian pengiriman semua absen sekaligus, supaya satu halaman tidak membaca satu per satu."""
    wanted = set(ids)
    if not wanted:
        return {}
    grouped: dict[str, list[AttendanceClockEvent]] = defaultdict(list)
    for event in db.scalars(
        select(AttendanceClockEvent)
        .where(AttendanceClockEvent.attendance_id.in_(wanted))
        .order_by(AttendanceClockEvent.submitted_at, AttendanceClockEvent.id)
    ).all():
        grouped[event.attendance_id].append(event)
    return grouped


def delete_events(db: Session, attendance_id: str) -> None:
    db.execute(delete(AttendanceClockEvent).where(AttendanceClockEvent.attendance_id == attendance_id))


def find_user(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def find_slot(db: Session, day: date, shift_code_id: str | None, user_id: str) -> Attendance | None:
    return db.scalar(
        select(Attendance).where(
            Attendance.date == day,
            Attendance.shift_code_id == shift_code_id,
            Attendance.user_id == user_id,
        )
    )


def find_schedule_id(db: Session, user_id: str, day: date, shift_code_id: str | None) -> str | None:
    return db.scalar(
        select(Schedule.id).where(
            Schedule.user_id == user_id,
            Schedule.date == day,
            Schedule.shift_code_id == shift_code_id,
        )
    )


def schedules_by_id(db: Session, ids: Iterable[str | None]) -> dict[str, Schedule]:
    wanted = {item for item in ids if item}
    if not wanted:
        return {}
    return {schedule.id: schedule for schedule in db.scalars(select(Schedule).where(Schedule.id.in_(wanted))).all()}


def codes_by_id(db: Session, ids: Iterable[str | None]) -> dict[str, ShiftCode]:
    wanted = {item for item in ids if item}
    if not wanted:
        return {}
    return {code.id: code for code in db.scalars(select(ShiftCode).where(ShiftCode.id.in_(wanted))).all()}


def outlets_by_id(db: Session, ids: Iterable[str]) -> dict[str, Outlet]:
    wanted = set(ids)
    if not wanted:
        return {}
    return {outlet.id: outlet for outlet in db.scalars(select(Outlet).where(Outlet.id.in_(wanted))).all()}
