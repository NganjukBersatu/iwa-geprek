"""Riwayat pengisian tugas outlet untuk admin: daftar per hari dan isi jawabannya."""
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import ColumnElement, Exists, Row, Select, and_, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.clock import today
from app.core.errors import DomainError
from app.core.period import month_bounds
from app.core.search import contains
from app.core.sorting import SqlSorting
from app.core.user_names import user_names
from app.employee.batches.constants import KIND_TOGGLE, TOGGLE_PROBLEM
from app.employee.batches.messages import NOT_FOUND
from app.employee.batches.run_content import AnswerRow, answers_of, problem_count
from app.models.outlet import Outlet
from app.models.outlet_batch import OutletBatch, OutletBatchAnswer, OutletBatchRun, OutletBatchRunVersion
from app.models.user import User
from app.models.task import Task, TaskStatus
from web.management.batches import messages
from web.management.batches.constants import FOLLOW_UP_NONE, FOLLOW_UP_OPEN, MAX_FOLLOW_UPS, MAX_VERSIONS, NOT_FOUND_STATUS
from web.management.batches.domain import RunQuery

# Terbaru di atas; pengisian di hari yang sama diurutkan dari yang paling akhir selesai.
SORTING = SqlSorting(
    columns={
        "day": OutletBatchRun.day,
        "name": OutletBatch.name,
        "outlet": Outlet.name,
        "completed": OutletBatchRun.completed_at,
    },
    default=(OutletBatchRun.day.desc(), OutletBatchRun.completed_at.desc()),
    tiebreak=OutletBatchRun.id,
)


@dataclass(frozen=True)
class RunRow:
    id: str
    kind: str
    day: date
    completed_at: datetime
    batch_name: str
    outlet_id: str
    outlet_name: str
    completer_name: str | None
    problems: int
    follow_up_total: int
    follow_up_open: int
    cancelled: bool
    version_count: int
    fixed_by: str | None
    fixed_at: datetime | None
    last_action: str | None


@dataclass(frozen=True)
class LastChange:
    """Perubahan terakhir sebuah pengisian dan jumlah versi lamanya."""

    count: int
    changed_by_id: str | None
    changed_at: datetime
    action: str


@dataclass(frozen=True)
class VersionRow:
    """Isi pengisian sebelum satu perbaikan atau pembatalan."""

    number: int
    action: str
    changed_by: str | None
    changed_at: datetime
    completed_by: str | None
    completed_at: datetime
    answers: list[AnswerRow]


@dataclass(frozen=True)
class FollowUpRow:
    """Tugas karyawan yang dibuat untuk menindaklanjuti satu pengisian."""

    task_id: str
    number: int
    title: str
    assignee_name: str | None
    done: bool
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class RunPage:
    items: list[RunRow]
    total: int


def day_window(first: date | None, last: date | None) -> tuple[date, date]:
    """Tanpa tanggal sama sekali daftar memakai bulan ini; satu sisi yang kosong mengikuti sisi lainnya."""
    if first is None and last is None:
        return month_bounds(today())
    first = first or last
    last = last or first
    if last < first:
        raise DomainError(messages.RANGE_INVALID)
    return first, last


def _runs() -> Select:
    return (
        select(
            OutletBatchRun.id,
            OutletBatchRun.day,
            OutletBatchRun.completed_at,
            OutletBatchRun.completed_by_id,
            OutletBatch.name,
            OutletBatch.outlet_id,
            Outlet.name,
            OutletBatch.kind,
            OutletBatchRun.cancelled_at,
        )
        .join(OutletBatch, OutletBatch.id == OutletBatchRun.batch_id)
        .join(Outlet, Outlet.id == OutletBatch.outlet_id)
    )


def _run_row(row: Row, names: dict[str, str], problems: int, follow_ups: tuple[int, int], change: LastChange | None) -> RunRow:
    run_id, day, completed_at, completer_id, batch_name, outlet_id, outlet_name, kind, cancelled_at = row
    return RunRow(
        id=run_id,
        kind=kind,
        day=day,
        completed_at=completed_at,
        batch_name=batch_name,
        outlet_id=outlet_id,
        outlet_name=outlet_name,
        completer_name=names.get(completer_id) if completer_id else None,
        problems=problems,
        follow_up_total=follow_ups[0],
        follow_up_open=follow_ups[1],
        cancelled=cancelled_at is not None,
        version_count=change.count if change else 0,
        fixed_by=names.get(change.changed_by_id) if change and change.changed_by_id else None,
        fixed_at=change.changed_at if change else None,
        last_action=change.action if change else None,
    )


def _problems(db: Session, run_ids: list[str]) -> dict[str, int]:
    """Jumlah isian Oke/Bermasalah yang dijawab Bermasalah, sekaligus untuk satu halaman."""
    if not run_ids:
        return {}
    rows = db.execute(
        select(OutletBatchAnswer.run_id, func.count())
        .where(
            OutletBatchAnswer.run_id.in_(run_ids),
            OutletBatchAnswer.item_kind == KIND_TOGGLE,
            OutletBatchAnswer.value == TOGGLE_PROBLEM,
        )
        .group_by(OutletBatchAnswer.run_id)
    ).all()
    return {run_id: count for run_id, count in rows}


def _last_changes(db: Session, run_ids: list[str]) -> dict[str, LastChange]:
    """Versi terakhir dan jumlah versi per pengisian, sekaligus untuk satu halaman."""
    if not run_ids:
        return {}
    same_run = OutletBatchRunVersion.run_id
    ranked = (
        select(
            same_run,
            OutletBatchRunVersion.changed_by_id,
            OutletBatchRunVersion.changed_at,
            OutletBatchRunVersion.action,
            func.count().over(partition_by=same_run).label("total"),
            func.row_number().over(partition_by=same_run, order_by=OutletBatchRunVersion.number.desc()).label("place"),
        )
        .where(same_run.in_(run_ids))
        .subquery()
    )
    rows = db.execute(select(ranked.c.run_id, ranked.c.total, ranked.c.changed_by_id, ranked.c.changed_at, ranked.c.action).where(ranked.c.place == 1)).all()
    return {
        run_id: LastChange(count=total, changed_by_id=changed_by_id, changed_at=changed_at, action=action)
        for run_id, total, changed_by_id, changed_at, action in rows
    }


def _versions(db: Session, run_id: str) -> list[VersionRow]:
    """Terbaru di atas dan dibatasi, supaya rincian tetap ringan walau satu pengisian diperbaiki berkali-kali."""
    rows = db.scalars(
        select(OutletBatchRunVersion).where(OutletBatchRunVersion.run_id == run_id).order_by(OutletBatchRunVersion.number.desc()).limit(MAX_VERSIONS)
    ).all()
    names = user_names(db, [user_id for row in rows for user_id in (row.changed_by_id, row.completed_by_id)])
    return [
        VersionRow(
            number=row.number,
            action=row.action,
            changed_by=names.get(row.changed_by_id) if row.changed_by_id else None,
            changed_at=row.changed_at,
            completed_by=names.get(row.completed_by_id) if row.completed_by_id else None,
            completed_at=row.completed_at,
            answers=[
                AnswerRow(label=answer.get("label") or "", kind=answer.get("kind") or "", value=answer.get("value"), photo_path=answer.get("photo_path"))
                for answer in row.answers
            ],
        )
        for row in rows
    ]


def _follow_up_counts(db: Session, run_ids: list[str]) -> dict[str, tuple[int, int]]:
    """Jumlah tugas tindak lanjut dan yang belum selesai per pengisian, sekaligus untuk satu halaman."""
    if not run_ids:
        return {}
    rows = db.execute(
        select(Task.source_run_id, func.count(), func.sum(case((Task.status == TaskStatus.OPEN, 1), else_=0)))
        .where(Task.source_run_id.in_(run_ids))
        .group_by(Task.source_run_id)
    ).all()
    return {run_id: (total, int(pending or 0)) for run_id, total, pending in rows}


def _follow_ups(db: Session, run_id: str) -> list[FollowUpRow]:
    """Berurutan dari yang pertama dibuat dan dibatasi, supaya rincian tetap ringan walau satu pengisian ditindaklanjuti berkali-kali."""
    rows = db.execute(
        select(Task.id, Task.title, Task.assignee_id, Task.status, Task.due_at, Task.completed_at, Task.created_at)
        .where(Task.source_run_id == run_id)
        .order_by(Task.created_at, Task.id)
        .limit(MAX_FOLLOW_UPS)
    ).all()
    names = user_names(db, [row.assignee_id for row in rows])
    return [
        FollowUpRow(
            task_id=row.id,
            number=number,
            title=row.title,
            assignee_name=names.get(row.assignee_id),
            done=row.status == TaskStatus.DONE,
            due_at=row.due_at,
            completed_at=row.completed_at,
            created_at=row.created_at,
        )
        for number, row in enumerate(rows, start=1)
    ]


def _follow_up(open_only: bool = False) -> Exists:
    found = exists().where(Task.source_run_id == OutletBatchRun.id)
    return found.where(Task.status == TaskStatus.OPEN) if open_only else found


def _follow_up_state(state: str) -> ColumnElement[bool]:
    if state == FOLLOW_UP_NONE:
        return ~_follow_up()
    if state == FOLLOW_UP_OPEN:
        return _follow_up(open_only=True)
    return and_(_follow_up(), ~_follow_up(open_only=True))


def _problem_answer() -> Exists:
    return exists().where(
        OutletBatchAnswer.run_id == OutletBatchRun.id, OutletBatchAnswer.item_kind == KIND_TOGGLE, OutletBatchAnswer.value == TOGGLE_PROBLEM
    )


def run_page(db: Session, wanted: RunQuery, sort: str | None, page: int, size: int) -> RunPage:
    query = _runs().where(OutletBatchRun.day >= wanted.first, OutletBatchRun.day <= wanted.last)
    if wanted.outlet_id is not None:
        query = query.where(OutletBatch.outlet_id == wanted.outlet_id)
    if wanted.kind is not None:
        query = query.where(OutletBatch.kind == wanted.kind)
    if wanted.batch_id is not None:
        query = query.where(OutletBatchRun.batch_id == wanted.batch_id)
    if wanted.problems is not None:
        query = query.where(_problem_answer() if wanted.problems else ~_problem_answer())
    if wanted.follow_up is not None:
        query = query.where(_follow_up_state(wanted.follow_up))
    if wanted.search:
        filler = exists().where(User.id == OutletBatchRun.completed_by_id, or_(contains(User.name, wanted.search), contains(User.username, wanted.search)))
        query = query.where(or_(contains(OutletBatch.name, wanted.search), filler))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(*SORTING.order_by(sort)).offset((page - 1) * size).limit(size)).all()
    run_ids = [row.id for row in rows]
    problems = _problems(db, run_ids)
    follow_ups = _follow_up_counts(db, run_ids)
    changes = _last_changes(db, run_ids)
    names = user_names(db, [*(row.completed_by_id for row in rows), *(change.changed_by_id for change in changes.values())])
    return RunPage(
        items=[_run_row(row, names, problems.get(row.id, 0), follow_ups.get(row.id, (0, 0)), changes.get(row.id)) for row in rows], total=total
    )


def run_detail(db: Session, user: User, run_id: str) -> tuple[RunRow, list[AnswerRow], list[FollowUpRow], list[VersionRow]]:
    """Admin yang terikat cabang tidak pernah sampai ke pengisian cabang lain, walau tahu id-nya."""
    row = db.execute(_runs().where(OutletBatchRun.id == run_id)).first()
    locked = user.locked_outlet_id
    if row is None or (locked and row.outlet_id != locked):
        raise DomainError(NOT_FOUND, status=NOT_FOUND_STATUS)
    answers = answers_of(db, row.id)
    problems = problem_count(answers)
    follow_ups = _follow_up_counts(db, [row.id]).get(row.id, (0, 0))
    change = _last_changes(db, [row.id]).get(row.id)
    names = user_names(db, [row.completed_by_id, change.changed_by_id if change else None])
    return _run_row(row, names, problems, follow_ups, change), answers, _follow_ups(db, row.id), _versions(db, row.id)
