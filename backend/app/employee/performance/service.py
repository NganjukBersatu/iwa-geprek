"""Builds the charts over the person's pay cycle, the one before it, or everything since they joined."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.clock import local_date
from app.employee.attendance.summary.domain import Day
from app.employee.attendance.summary.service import build_days_many
from app.employee.overtime.ledger import Entry, merged_minutes, month_entries_many
from app.employee.performance import cycle, repository
from app.employee.performance.constants import DAYS_PER_WEEK, PERCENT
from app.employee.performance.domain import Bucket, Composition, Performance, Range
from app.employee.performance.rating import service as rating
from app.employee.performance.rating.scheduled import Key, by_day_many
from app.models.attendance import AttendanceStatus
from app.models.user import User
from app.models.task import Task, TaskStatus

UNEXCUSED = (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.ABSENT)


def _anchors(db: Session, users: list[User], today: date) -> dict[str, date]:
    """The day each cycle counts from: the joined date, else the first day the person appears in the data."""
    firsts = repository.first_activity_dates(db, [user.id for user in users if user.joined_date is None])
    return {user.id: user.joined_date or firsts.get(user.id) or today for user in users}


def _period(anchor: date, range_: Range, today: date) -> tuple[date, date]:
    if range_ is Range.ALL:
        return min(anchor, today), today
    if range_ is Range.PREVIOUS:
        return cycle.previous(anchor.day, today)
    return cycle.containing(anchor.day, today)


def _spans(range_: Range, anchor: date, first: date, until: date) -> list[tuple[date, date]]:
    """Weeks from the first day of a cycle; whole pay cycles when the range covers everything."""
    spans: list[tuple[date, date]] = []
    if range_ is Range.ALL:
        start = first
        while start <= until:
            end = min(cycle.containing(anchor.day, start)[1], until)
            spans.append((start, end))
            start = end + timedelta(days=1)
        return spans
    start = first
    while start <= until:
        spans.append((start, min(start + timedelta(days=DAYS_PER_WEEK - 1), until)))
        start += timedelta(days=DAYS_PER_WEEK)
    return spans


def _percent(days: list[Day]) -> int | None:
    counted = [day for day in days if day.status in UNEXCUSED]
    if not counted:
        return None
    on_time = sum(1 for day in counted if day.status == AttendanceStatus.PRESENT)
    return round(PERCENT * on_time / len(counted))


def _tasks_in(tasks: list[Task], first: date, until: date) -> list[Task]:
    return [task for task in tasks if first <= local_date(task.created_at) <= until]


def _completed_on(tasks: list[Task], first: date, last: date) -> int:
    return sum(
        1
        for task in tasks
        if task.status == TaskStatus.DONE and task.completed_at is not None and first <= local_date(task.completed_at) <= last
    )


def _bucket(span: tuple[date, date], days: list[Day], entries: list[Entry], tasks: list[Task]) -> Bucket:
    start, end = span
    in_span = [day for day in days if start <= day.date <= end]
    return Bucket(
        start=start,
        end=end,
        on_time_percent=_percent(in_span),
        work_minutes=sum(day.work_minutes or 0 for day in in_span),
        overtime_minutes=merged_minutes([entry for entry in entries if start <= entry.date <= end]),
        tasks_done=_completed_on(tasks, start, end),
    )


@dataclass(frozen=True)
class _Window:
    """The days one person is measured over: [first, until] is read, [first, last] is the period shown."""

    anchor: date
    first: date
    last: date
    until: date


def _window(anchor: date, range_: Range, today: date) -> _Window:
    first, last = _period(anchor, range_, today)
    return _Window(anchor=anchor, first=max(first, anchor), last=last, until=min(last, today))


def _assemble(
    user_id: str, range_: Range, window: _Window, days: list[Day], entries: list[Entry], tasks: list[Task], scheduled: dict[Key, int], at: datetime
) -> Performance:
    first, until = window.first, window.until

    def count(*statuses: AttendanceStatus) -> int:
        return sum(1 for day in days if day.status in statuses)

    buckets = [_bucket(span, days, entries, tasks) for span in _spans(range_, window.anchor, first, until)]
    return Performance(
        range=range_,
        start=first,
        end=window.last,
        counted_days=len(days),
        buckets=buckets,
        composition=Composition(
            on_time=count(AttendanceStatus.PRESENT),
            late=count(AttendanceStatus.LATE),
            leave=count(AttendanceStatus.PERMIT, AttendanceStatus.SICK),
            absent=count(AttendanceStatus.ABSENT),
        ),
        tasks_assigned=len(tasks),
        tasks_done=_completed_on(tasks, first, until),
        rating=rating.build(user_id, days, tasks, scheduled, at),
    )


def build_many(db: Session, users: list[User], range_: Range, at: datetime) -> dict[str, Performance]:
    """Every person over their own cycle; the data is read once for the widest span, so the queries do not grow with the people."""
    today = local_date(at)
    anchors = _anchors(db, users, today)
    windows = {user.id: _window(anchors[user.id], range_, today) for user in users}
    measured = [user_id for user_id, window in windows.items() if window.until >= window.first]
    built = {
        user_id: Performance(range_, window.first, window.last, 0, [], Composition(0, 0, 0, 0), 0, 0, rating.empty())
        for user_id, window in windows.items()
        if user_id not in measured
    }
    if not measured:
        return built

    low = min(windows[user_id].first for user_id in measured)
    high = max(windows[user_id].until for user_id in measured)
    days_of = build_days_many(db, measured, low, high, today)
    entries_of = month_entries_many(db, measured, low, high)
    tasks_of = repository.assigned_tasks_many(db, measured)
    scheduled_of = by_day_many(db, measured, low, high)
    for user_id in measured:
        window = windows[user_id]

        def inside(day: date, window: _Window = window) -> bool:
            return window.first <= day <= window.until

        built[user_id] = _assemble(
            user_id,
            range_,
            window,
            [day for day in days_of[user_id][0] if inside(day.date)],
            [entry for entry in entries_of[user_id] if inside(entry.date)],
            _tasks_in(tasks_of[user_id], window.first, window.until),
            {key: minutes for key, minutes in scheduled_of[user_id].items() if inside(key[0])},
            at,
        )
    return built


def build(db: Session, user: User, range_: Range, at: datetime) -> Performance:
    return build_many(db, [user], range_, at)[user.id]
