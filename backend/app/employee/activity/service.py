"""Merges the sources into one newest-first page."""
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from app.employee.activity import sources
from app.employee.activity.domain import Event, Group, Page

SOURCES: dict[Group, Callable[[Session, str, datetime | None, int], list[Event]]] = {
    Group.ATTENDANCE: sources.attendance,
    Group.TASK: sources.tasks,
    Group.OVERTIME: sources.overtime,
    Group.LEAVE: sources.leave,
    Group.OPERATIONS: sources.operations,
}


def page(db: Session, user_id: str, before: datetime | None, limit: int, group: Group | None) -> Page:
    chosen = [group] if group is not None else list(SOURCES)
    events: list[Event] = []
    for each in chosen:
        events += SOURCES[each](db, user_id, before, limit)
    events.sort(key=lambda event: event.at, reverse=True)
    events = events[:limit]
    return Page(events=events, next_before=events[-1].at if len(events) == limit else None)
