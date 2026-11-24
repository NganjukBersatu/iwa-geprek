"""Everything counted as overtime for one person: scheduled hours on days worked, and unplanned entries."""
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.clock import SECONDS_PER_MINUTE, as_aware
from app.employee.overtime import repository
from app.employee.schedule.assignment import overtime_window
from app.models.overtime import Overtime


@dataclass(frozen=True)
class Entry:
    id: str
    date: date
    start_at: datetime
    end_at: datetime
    scheduled: bool
    note: str | None


def unplanned_entry(item: Overtime) -> Entry:
    return Entry(item.id, item.date, as_aware(item.start_at), as_aware(item.end_at), False, item.note)


def month_entries_many(db: Session, user_ids: list[str], first: date, last: date) -> dict[str, list[Entry]]:
    """The entries of every person asked for, in two queries however many people."""
    found: dict[str, list[Entry]] = {user_id: [] for user_id in user_ids}
    for item in repository.between(db, user_ids, first, last):
        if item.end_at:
            found[item.user_id].append(unplanned_entry(item))
    for schedule in repository.worked_schedules(db, user_ids, first, last):
        window = overtime_window(schedule)
        if window is not None:
            found[schedule.user_id].append(Entry(schedule.id, schedule.date, window[0], window[1], True, None))
    return {user_id: sorted(entries, key=lambda entry: entry.start_at, reverse=True) for user_id, entries in found.items()}


def month_entries(db: Session, user_id: str, first: date, last: date) -> list[Entry]:
    return month_entries_many(db, [user_id], first, last)[user_id]


def merged_minutes(entries: list[Entry]) -> int:
    """Total minutes, counting overlapping parts once."""
    total_seconds = 0.0
    covered_until: datetime | None = None
    for start, end in sorted((entry.start_at, entry.end_at) for entry in entries):
        if end <= start:
            continue
        if covered_until is None or start >= covered_until:
            total_seconds += (end - start).total_seconds()
            covered_until = end
        elif end > covered_until:
            total_seconds += (end - covered_until).total_seconds()
            covered_until = end
    return int(total_seconds // SECONDS_PER_MINUTE)


def scheduled_on(db: Session, user_id: str, day: date) -> Entry | None:
    """The overtime hours the schedule already holds for that day, whether or not the person has worked yet."""
    for schedule in repository.schedules_on(db, user_id, day):
        window = overtime_window(schedule)
        if window is not None:
            return Entry(schedule.id, schedule.date, window[0], window[1], True, None)
    return None
