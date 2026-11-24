"""Notices written when a task changes, and read when the person signs in or opens the app."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.employee.notices import constants, repository
from app.models.notice import Notice


def _add_overdue(db: Session, assignee_id: str, task_id: str, title: str, due_at: datetime) -> None:
    repository.add(db, [assignee_id], constants.TASK_OVERDUE, constants.TASK_KIND, task_id, title, due_at)


def task_created(db: Session, assignee_id: str, task_id: str, title: str, due_at: datetime | None, at: datetime) -> None:
    repository.add(db, [assignee_id], constants.TASK_ASSIGNED, constants.TASK_KIND, task_id, title, at)
    if due_at is not None:
        _add_overdue(db, assignee_id, task_id, title, due_at)


def due_changed(db: Session, assignee_id: str, task_id: str, title: str, due_at: datetime, at: datetime) -> None:
    """The overdue notice moves to the new deadline."""
    repository.delete_for_task(db, task_id, constants.TASK_OVERDUE)
    repository.add(db, [assignee_id], constants.DUE_CHANGED, constants.TASK_KIND, task_id, title, at)
    _add_overdue(db, assignee_id, task_id, title, due_at)


def task_done(db: Session, task_id: str) -> None:
    repository.delete_for_task(db, task_id, constants.TASK_OVERDUE)


def task_deleted(db: Session, task_id: str) -> None:
    repository.delete_for_task(db, task_id)


def visible(db: Session, user_id: str, at: datetime) -> list[Notice]:
    return repository.visible(db, user_id, at)


def mark_read(db: Session, user_id: str, ids: list[str], at: datetime) -> None:
    repository.mark_read(db, user_id, ids, at)
