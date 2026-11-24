"""The working and overtime windows of one scheduled assignment."""
from datetime import date, datetime

from app.core.clock import as_aware
from app.employee.schedule.window import window_from_code
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode

Window = tuple[datetime, datetime]


def work_window(day: date, schedule: Schedule | None, code: ShiftCode | None) -> Window | None:
    """The one shift window everything uses: the schedule's stored instants, else the code's clocks on that day."""
    if schedule is not None and schedule.starts_at and schedule.ends_at:
        return as_aware(schedule.starts_at), as_aware(schedule.ends_at)
    if code is None:
        return None
    return window_from_code(day, code.start_clock, code.end_clock, code.duration_minutes)


def stored_window(day: date, code: ShiftCode | None) -> tuple[datetime | None, datetime | None]:
    """The instants a schedule stores for its code on that day; empty without a code or its clocks."""
    window = window_from_code(day, code.start_clock, code.end_clock, code.duration_minutes) if code is not None else None
    return window if window else (None, None)


def overtime_window(schedule: Schedule) -> Window | None:
    """Always derived from the code's overtime clocks on the schedule's date, so no new column is needed."""
    code = schedule.shift_code
    if code is None:
        return None
    return window_from_code(schedule.date, code.overtime_start_clock, code.overtime_end_clock)
