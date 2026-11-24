"""Database reads and writes for notices."""
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.notice import Notice


def add(db: Session, user_ids: Iterable[str], kind: str, task_kind: str, task_id: str, title: str, show_at: datetime) -> None:
    for user_id in user_ids:
        db.add(Notice(user_id=user_id, kind=kind, task_kind=task_kind, task_id=task_id, title=title, show_at=show_at))


def visible(db: Session, user_id: str, at: datetime) -> list[Notice]:
    """Notices whose time has come and that the person has not read, oldest first."""
    return list(
        db.scalars(
            select(Notice)
            .where(Notice.user_id == user_id, Notice.show_at <= at, Notice.read_at.is_(None))
            .order_by(Notice.show_at)
        ).all()
    )


def mark_read(db: Session, user_id: str, ids: list[str], at: datetime) -> None:
    """Only the person's own unread notices are marked."""
    db.execute(
        update(Notice)
        .where(Notice.user_id == user_id, Notice.id.in_(ids), Notice.read_at.is_(None))
        .values(read_at=at)
        .execution_options(synchronize_session=False)
    )


def delete_for_task(db: Session, task_id: str, kind: str | None = None) -> None:
    """Every notice of a task, or only those of one kind."""
    conditions = [Notice.task_id == task_id]
    if kind is not None:
        conditions.append(Notice.kind == kind)
    db.execute(delete(Notice).where(*conditions).execution_options(synchronize_session=False))

