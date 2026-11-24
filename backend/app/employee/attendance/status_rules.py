"""Applies the lateness rule to a record that has a clock-in."""
from sqlalchemy.orm import Session

from app.employee.attendance import repository
from app.employee.attendance.lateness import minutes_late
from app.employee.attendance.policy import BranchPolicy
from app.employee.schedule.assignment import work_window
from app.models.attendance import PRESENT_STATUSES, Attendance


def refresh_status(db: Session, record: Attendance) -> None:
    """Leaves leave and absence statuses alone, and records without a scheduled start."""
    if record.status not in PRESENT_STATUSES or record.clock_in_at is None:
        return
    window = work_window(
        record.date, repository.schedule_of(db, record), repository.code_by_id(db, record.shift_code_id)
    )
    if window is None:
        return
    record.status = BranchPolicy.load(db, record.outlet_id).status_for(minutes_late(record.clock_in_at, window[0]))
