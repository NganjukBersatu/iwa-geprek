"""Database reads for the monthly summary."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


def records_between(db: Session, user_ids: list[str], first: date, last: date) -> list[Attendance]:
    """The records of all the people asked for in the range: one query, however many people."""
    return list(
        db.scalars(
            select(Attendance)
            .where(Attendance.user_id.in_(user_ids), Attendance.date >= first, Attendance.date <= last)
            .order_by(Attendance.date, Attendance.created_at)
        ).all()
    )


def schedules_between(db: Session, user_ids: list[str], first: date, last: date) -> list[Schedule]:
    return list(
        db.scalars(
            select(Schedule).where(Schedule.user_id.in_(user_ids), Schedule.date >= first, Schedule.date <= last)
        ).all()
    )


def codes_by_id(db: Session, code_ids: set[str]) -> dict[str, ShiftCode]:
    if not code_ids:
        return {}
    return {code.id: code for code in db.scalars(select(ShiftCode).where(ShiftCode.id.in_(code_ids))).all()}
