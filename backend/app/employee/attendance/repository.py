"""Database reads for attendance."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import PRESENT_STATUSES, Attendance
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


def find_open(db: Session, user_id: str) -> Attendance | None:
    """The newest clock-in without a clock-out, however old it is."""
    return db.scalar(
        select(Attendance)
        .where(
            Attendance.user_id == user_id,
            Attendance.clock_in_at.is_not(None),
            Attendance.clock_out_at.is_(None),
        )
        .order_by(Attendance.clock_in_at.desc())
        .limit(1)
    )


def open_present_records(db: Session, user_id: str) -> list[Attendance]:
    records = db.scalars(
        select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.clock_in_at.is_not(None),
            Attendance.clock_out_at.is_(None),
        )
    ).all()
    return [record for record in records if record.status in PRESENT_STATUSES]


def pending_notices(db: Session, user_id: str) -> list[Attendance]:
    """Records the system closed that the employee has not been told about yet."""
    return list(
        db.scalars(
            select(Attendance)
            .where(
                Attendance.user_id == user_id,
                Attendance.auto_closed.is_(True),
                Attendance.notice_seen.is_(False),
            )
            .order_by(Attendance.date, Attendance.clock_in_at)
        ).all()
    )


def find_reusable(db: Session, schedule: Schedule, user_id: str) -> Attendance | None:
    """A record for this assignment that has no clock-in yet, such as a pre-filed leave."""
    return db.scalar(
        select(Attendance).where(
            Attendance.date == schedule.date,
            Attendance.shift_code_id == schedule.shift_code_id,
            Attendance.user_id == user_id,
            Attendance.clock_in_at.is_(None),
        )
    )


def last_closed(db: Session, user_id: str) -> Attendance | None:
    return db.scalar(
        select(Attendance)
        .where(
            Attendance.user_id == user_id,
            Attendance.clock_in_at.is_not(None),
            Attendance.clock_out_at.is_not(None),
        )
        .order_by(Attendance.clock_out_at.desc())
        .limit(1)
    )


def schedule_of(db: Session, record: Attendance | None) -> Schedule | None:
    if record is None or record.schedule_id is None:
        return None
    return db.get(Schedule, record.schedule_id)


def code_by_id(db: Session, code_id: str | None) -> ShiftCode | None:
    return db.get(ShiftCode, code_id) if code_id else None


