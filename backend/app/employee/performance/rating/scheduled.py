"""Scheduled minutes of each shift, taken from the shared shift window."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.clock import minutes_between
from app.employee.attendance.summary import repository
from app.employee.schedule.assignment import work_window

Key = tuple[date, str | None]


def by_day_many(db: Session, user_ids: list[str], first: date, last: date) -> dict[str, dict[Key, int]]:
    """Scheduled minutes keyed by date and shift code, the same pair a summary day carries, for every person in one query."""
    minutes: dict[str, dict[Key, int]] = {user_id: {} for user_id in user_ids}
    if not user_ids:
        return minutes
    for schedule in repository.schedules_between(db, user_ids, first, last):
        window = work_window(schedule.date, schedule, schedule.shift_code)
        scheduled = minutes_between(*window) if window else None
        if scheduled:
            code = schedule.shift_code.code if schedule.shift_code else None
            minutes[schedule.user_id].setdefault((schedule.date, code), scheduled)
    return minutes
