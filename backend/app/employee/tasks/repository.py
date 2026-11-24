"""Database reads and small writes for tasks."""
from collections.abc import Iterable
from datetime import date, datetime

from sqlalchemy import ColumnElement, case, func, or_, select
from sqlalchemy.orm import Session

from app.core import protection
from app.core.date_range import range_end, range_start
from app.core.search import contains
from app.core.sorting import SqlSorting
from app.employee.tasks.domain import FollowUpPlace, SourceRun, TaskQuery
from app.models.outlet import Outlet
from app.models.outlet_batch import OutletBatch, OutletBatchRun
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.task_attachment import TaskAttachment


def date_window(first: date | None, last: date | None) -> tuple[datetime | None, datetime | None]:
    """The start and the end (exclusive) of a range of whole days; a side left out stays open."""
    return (range_start(first) if first else None, range_end(last) if last else None)


def _within(column: ColumnElement, query: TaskQuery) -> list[ColumnElement]:
    conditions = []
    if query.start is not None:
        conditions.append(column >= query.start)
    if query.end is not None:
        conditions.append(column < query.end)
    return conditions


def _matches(term: str) -> ColumnElement:
    """The words may be in the title, the text, or the name of whoever is given, wrote, or finished the task."""
    return or_(
        contains(Task.title, term),
        contains(Task.description, term),
        Task.assignee.has(contains(User.name, term)),
        Task.creator.has(contains(User.name, term)),
    )


_COLUMNS = {
    "title": Task.title,
    "outlet": select(Outlet.name).where(Outlet.id == Task.outlet_id).scalar_subquery(),
    "creator": select(func.coalesce(User.name, User.username)).where(User.id == Task.creator_id).scalar_subquery(),
}
# Open tasks by nearest deadline, those without one last; finished ones newest first.
OPEN_SORTING = SqlSorting(columns={**_COLUMNS, "moment": Task.due_at}, default=(Task.due_at.asc().nulls_last(), Task.created_at.desc()), tiebreak=Task.id)
DONE_SORTING = SqlSorting(
    columns={**_COLUMNS, "moment": Task.completed_at}, default=(func.coalesce(Task.completed_at, Task.created_at).desc(),), tiebreak=Task.id
)


def _order(user_id: str, sorting: SqlSorting, sort: str | None) -> list[ColumnElement]:
    """Without a chosen sort a person's own tasks come first, like their own rows in the schedule."""
    order = sorting.order_by(sort)
    if sort:
        return order
    return [case((Task.assignee_id == user_id, 0), else_=1), *order]


def task_page(db: Session, user_id: str, query: TaskQuery, sort: str | None, page: int, size: int) -> tuple[list[Task], int]:
    """A person's own tasks always show, even when their branch differs from the one asked for."""
    day = Task.completed_at if query.done else func.coalesce(Task.due_at, Task.created_at)
    filters = [Task.status == (TaskStatus.DONE if query.done else TaskStatus.OPEN), *_within(day, query)]
    if query.outlet_id is not None:
        filters.append(or_(Task.outlet_id == query.outlet_id, Task.assignee_id == user_id))
    if query.assignee_id is not None:
        filters.append(Task.assignee_id == query.assignee_id)
    if query.search:
        filters.append(_matches(query.search))
    sorting = DONE_SORTING if query.done else OPEN_SORTING
    total = db.scalar(select(func.count()).select_from(Task).where(*filters)) or 0
    rows = db.scalars(select(Task).where(*filters).order_by(*_order(user_id, sorting, sort)).offset((page - 1) * size).limit(size)).all()
    return list(rows), total


def own_tasks(db: Session, user_id: str, limit: int) -> list[Task]:
    """Only the pending ones, so finished tasks never push a real pending one out of the dashboard's capped page."""
    return list(
        db.scalars(
            select(Task).where(Task.assignee_id == user_id, Task.status == TaskStatus.OPEN).order_by(Task.created_at.desc()).limit(limit)
        ).all()
    )


def attachments_by_task(db: Session, task_ids: Iterable[str]) -> dict[str, list[TaskAttachment]]:
    wanted = list(task_ids)
    if not wanted:
        return {}
    rows = db.scalars(
        select(TaskAttachment)
        .where(TaskAttachment.personal_task_id.in_(wanted))
        .order_by(TaskAttachment.position, TaskAttachment.created_at)
    ).all()
    grouped: dict[str, list[TaskAttachment]] = {}
    for row in rows:
        grouped.setdefault(row.personal_task_id, []).append(row)
    return grouped


def attachments_of(db: Session, task_id: str) -> list[TaskAttachment]:
    return list(
        db.scalars(
            select(TaskAttachment)
            .where(TaskAttachment.personal_task_id == task_id)
            .order_by(TaskAttachment.position, TaskAttachment.created_at)
        ).all()
    )


def find_attachment(db: Session, attachment_id: str) -> TaskAttachment | None:
    return db.get(TaskAttachment, attachment_id)


def find_task(db: Session, task_id: str) -> Task | None:
    return db.get(Task, task_id)


def outlet_names(db: Session, outlet_ids: Iterable[str | None]) -> dict[str, str]:
    wanted = {outlet_id for outlet_id in outlet_ids if outlet_id}
    if not wanted:
        return {}
    rows = db.execute(select(Outlet.id, Outlet.name).where(Outlet.id.in_(wanted))).all()
    return {outlet_id: name for outlet_id, name in rows}


def source_runs(db: Session, run_ids: Iterable[str | None]) -> dict[str, SourceRun]:
    """Pengisian asal untuk satu halaman tugas, dalam satu query."""
    wanted = {run_id for run_id in run_ids if run_id}
    if not wanted:
        return {}
    rows = db.execute(
        select(OutletBatchRun.id, OutletBatch.name, OutletBatch.kind, OutletBatchRun.day, OutletBatch.outlet_id)
        .join(OutletBatch, OutletBatch.id == OutletBatchRun.batch_id)
        .where(OutletBatchRun.id.in_(wanted))
    ).all()
    return {run_id: SourceRun(id=run_id, batch_name=name, kind=kind, day=day, outlet_id=outlet_id) for run_id, name, kind, day, outlet_id in rows}


def follow_up_places(db: Session, run_ids: Iterable[str | None]) -> dict[str, FollowUpPlace]:
    """Nomor urut tiap tugas tindak lanjut dari pengisian-pengisian ini, dalam satu query."""
    wanted = {run_id for run_id in run_ids if run_id}
    if not wanted:
        return {}
    number = func.row_number().over(partition_by=Task.source_run_id, order_by=(Task.created_at, Task.id))
    total = func.count().over(partition_by=Task.source_run_id)
    rows = db.execute(select(Task.id, number, total).where(Task.source_run_id.in_(wanted))).all()
    return {task_id: FollowUpPlace(number=place, total=count) for task_id, place, count in rows}


def all_outlets(db: Session) -> list[Outlet]:
    return list(db.scalars(select(Outlet).order_by(Outlet.name)).all())


def find_outlet_row(db: Session, outlet_id: str) -> Outlet | None:
    return db.get(Outlet, outlet_id)


def active_user(db: Session, outlet_id: str | None) -> list[User]:
    filters = [User.is_active.is_(True), protection.schedulable()]
    if outlet_id is not None:
        filters.append(User.outlet_id == outlet_id)
    return list(db.scalars(select(User).where(*filters).order_by(User.name, User.username)).all())


def find_user(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)
