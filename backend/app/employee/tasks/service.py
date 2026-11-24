"""Listing, creating, changing, and finishing the tasks given to a person."""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core import live, protection, uploads
from app.core.clock import as_aware, now, today
from app.core.errors import DomainError
from app.core.period import month_bounds
from app.core.uploads import UploadedFile
from app.employee.batches.run_content import RunContent, run_content
from app.employee.notices import service as notices
from app.employee.tasks import access, messages, repository
from app.employee.tasks.constants import (
    LEGACY_ASSIGNMENT_PREFIX,
    LEGACY_COMPLETION_PREFIX,
    MAX_TEXT_LENGTH,
    MAX_TITLE_LENGTH,
    MEDIA_FOLDER,
)
from app.employee.tasks.domain import NewTask, TaskChanges, TaskEntry, TaskOptions, TaskPage, TaskQuery
from app.employee.tasks.entries import task_entry
from app.employee.tasks.upload import RULE
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskType
from app.models.task_attachment import TaskAttachment

FORBIDDEN = 403
# Riwayat pengisian menampilkan status tindak lanjutnya, jadi ikut dimuat ulang saat tugas tindak lanjut berubah.
RUN_TABLE = "outlet_batch_runs"
NOT_FOUND = 404


def _clean_title(title: str | None) -> str:
    cleaned = (title or "").strip()
    if not cleaned:
        raise DomainError(messages.TITLE_REQUIRED)
    return cleaned[:MAX_TITLE_LENGTH]


def _clean_text(text: str | None) -> str | None:
    return (text or "").strip()[:MAX_TEXT_LENGTH] or None


def _entries(db: Session, rows: list[Task]) -> list[TaskEntry]:
    attachments = repository.attachments_by_task(db, [row.id for row in rows])
    names = repository.outlet_names(db, [row.outlet_id for row in rows])
    run_ids = [row.source_run_id for row in rows]
    sources = repository.source_runs(db, run_ids)
    places = repository.follow_up_places(db, run_ids)
    return [
        task_entry(row, attachments.get(row.id, []), names.get(row.outlet_id), sources.get(row.source_run_id), places.get(row.id))
        for row in rows
    ]


def _entry_of(db: Session, task: Task) -> TaskEntry:
    return _entries(db, [task])[0]


def _locate(db: Session, task_id: str) -> Task:
    task = repository.find_task(db, task_id)
    if task is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return task


def _done(task: Task) -> bool:
    return task.status == TaskStatus.DONE


def get(db: Session, user: User, task_id: str) -> TaskEntry:
    """One task; another branch's task answers as missing for someone bound to one branch, so its existence is not revealed."""
    task = _locate(db, task_id)
    locked = user.locked_outlet_id
    if locked and task.outlet_id != locked:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return _entry_of(db, task)


def list_tasks(db: Session, user: User, query: TaskQuery, sort: str | None, page: int, size: int) -> TaskPage:
    rows, total = repository.task_page(db, user.id, query, sort, page, size)
    return TaskPage(items=_entries(db, rows), total=total, page=page, size=size)


def task_query(
    done: bool,
    first: date | None,
    last: date | None,
    outlet_id: str | None,
    search: str | None,
    assignee_id: str | None,
) -> TaskQuery:
    """Without any date the list shows this month; that is only the starting scope, whatever the person narrows to."""
    if first and last and last < first:
        raise DomainError(messages.INVALID_RANGE)
    if first is None and last is None:
        first, last = month_bounds(today())
    start, end = repository.date_window(first, last)
    return TaskQuery(
        done=done,
        start=start,
        end=end,
        outlet_id=outlet_id,
        search=(search or "").strip() or None,
        assignee_id=assignee_id or None,
    )


def my_tasks(db: Session, user: User, size: int) -> TaskPage:
    """The tasks given to one person, newest first."""
    rows = repository.own_tasks(db, user.id, size)
    return TaskPage(items=_entries(db, rows), total=len(rows), page=1, size=size)


def options(db: Session, user: User, outlet_id: str | None) -> TaskOptions:
    locked = user.locked_outlet_id
    if locked:
        own = repository.find_outlet_row(db, locked)
        outlets = [own] if own is not None else []
    else:
        outlets = repository.all_outlets(db)
    manager = access.is_manager(user)
    return TaskOptions(
        outlets=outlets,
        assignees=repository.active_user(db, outlet_id) if manager else [],
        can_manage=manager,
    )


def _assignee_for(db: Session, user: User, assignee_id: str | None) -> User:
    if not assignee_id or assignee_id == user.id:
        return user
    if not access.is_manager(user):
        raise DomainError(messages.ASSIGN_NOT_ALLOWED, status=FORBIDDEN)
    assignee = repository.find_user(db, assignee_id)
    if assignee is None or not assignee.is_active:
        raise DomainError(messages.ASSIGNEE_NOT_FOUND, status=NOT_FOUND)
    locked = user.locked_outlet_id
    if locked and assignee.working_outlet_id != locked:
        raise DomainError(messages.ASSIGNEE_OTHER_BRANCH, status=FORBIDDEN)
    protection.ensure_schedulable(assignee)
    return assignee


def _source_run_id(db: Session, user: User, run_id: str | None) -> str | None:
    """Hanya pengelola yang menautkan tindak lanjut, dan hanya ke pengisian cabang yang boleh dilihatnya."""
    if not run_id:
        return None
    if not access.is_manager(user):
        raise DomainError(messages.ASSIGN_NOT_ALLOWED, status=FORBIDDEN)
    source = repository.source_runs(db, [run_id]).get(run_id)
    locked = user.locked_outlet_id
    if source is None or (locked and source.outlet_id != locked):
        raise DomainError(messages.SOURCE_NOT_FOUND)
    return source.id


def _signal_source(db: Session, task: Task) -> None:
    if task.source_run_id:
        live.mark(db, (RUN_TABLE,))


def _new_task(db: Session, user: User, data: NewTask, title: str) -> Task:
    assignee = _assignee_for(db, user, data.assignee_id)
    return Task(
        id=str(uuid.uuid4()),
        outlet_id=assignee.working_outlet_id,
        type=TaskType.ASSIGNMENT,
        status=TaskStatus.OPEN,
        title=title,
        description=_clean_text(data.description),
        assignee_id=assignee.id,
        creator_id=user.id,
        due_at=data.due_at,
        source_run_id=_source_run_id(db, user, data.source_run_id),
    )


def _ensure_can_edit(user: User, task: Task) -> None:
    if not access.can_edit(user, task.creator_id):
        raise DomainError(messages.NOT_YOURS, status=FORBIDDEN)


def _ensure_can_attach(user: User, task: Task) -> None:
    """Pembuat mengubah lampiran tugasnya; penerima membenahi bukti tugas yang sudah ia selesaikan."""
    if not access.can_edit(user, task.creator_id) and not access.can_fix(user, _done(task), task.assignee_id):
        raise DomainError(messages.NOT_YOURS, status=FORBIDDEN)


def _ensure_can_finish(user: User, task: Task, proof_count: int) -> None:
    if _done(task):
        raise DomainError(messages.ALREADY_DONE)
    if not access.can_complete(user, _done(task), task.assignee_id):
        raise DomainError(messages.NOT_YOURS, status=FORBIDDEN)
    if proof_count < 1:
        raise DomainError(messages.PROOF_REQUIRED)


def _mark_done(task: Task, note: str | None) -> None:
    task.completion_note = _clean_text(note)
    task.completed_at = now()
    task.status = TaskStatus.DONE


def _store_media(db: Session, user: User, task: Task, media: list[UploadedFile], first_position: int) -> None:
    """A file that did not really land cancels the whole change."""
    for offset, item in enumerate(media):
        attachment_id = str(uuid.uuid4())
        path = f"{MEDIA_FOLDER}/{task.id}/{attachment_id}{item.extension}"
        uploads.store(db, path, item, RULE)
        db.add(
            TaskAttachment(
                id=attachment_id,
                personal_task_id=task.id,
                kind=item.kind,
                path=path,
                position=first_position + offset,
                created_by_id=user.id,
            )
        )


def create(db: Session, user: User, data: NewTask, media: list[UploadedFile]) -> TaskEntry:
    """A task for oneself may be written first and finished later, or finished at once with its proof."""
    task = _new_task(db, user, data, _clean_title(data.title))
    if data.complete:
        _ensure_can_finish(user, task, proof_count=len(media))

    db.add(task)
    db.flush()
    _store_media(db, user, task, media, first_position=0)
    if data.complete:
        _mark_done(task, note=None)
    else:
        notices.task_created(db, task.assignee_id, task.id, task.title, task.due_at, now())
    _signal_source(db, task)
    db.commit()
    db.refresh(task)
    return _entry_of(db, task)


def update(db: Session, user: User, task_id: str, changes: TaskChanges) -> TaskEntry:
    task = _locate(db, task_id)
    _ensure_can_edit(user, task)
    if changes.title is not None:
        task.title = _clean_title(changes.title)
    if changes.description is not None:
        task.description = _clean_text(changes.description)
    if changes.due_at is not None and (task.due_at is None or as_aware(changes.due_at) != as_aware(task.due_at)):
        task.due_at = changes.due_at
        if not _done(task):
            notices.due_changed(db, task.assignee_id, task.id, task.title, task.due_at, now())
    _signal_source(db, task)
    db.commit()
    db.refresh(task)
    return _entry_of(db, task)


def complete(db: Session, user: User, task_id: str, note: str | None, media: list[UploadedFile]) -> TaskEntry:
    """The finisher must have uploaded at least one file of their own; the creator's examples do not count as proof."""
    task = _locate(db, task_id)
    rows = repository.attachments_of(db, task.id)
    own_proof = sum(1 for row in rows if row.created_by_id == user.id)
    _ensure_can_finish(user, task, proof_count=own_proof + len(media))

    _store_media(db, user, task, media, first_position=len(rows))
    _mark_done(task, note)
    notices.task_done(db, task.id)
    _signal_source(db, task)
    db.commit()
    db.refresh(task)
    return _entry_of(db, task)


def fix_completion(db: Session, user: User, task_id: str, note: str | None) -> TaskEntry:
    """Hanya catatannya yang berganti; waktu selesai tetap waktu tugas itu pertama kali diselesaikan."""
    task = _locate(db, task_id)
    if not access.can_fix(user, _done(task), task.assignee_id):
        raise DomainError(messages.NOT_YOURS, status=FORBIDDEN)
    task.completion_note = _clean_text(note)
    _signal_source(db, task)
    db.commit()
    db.refresh(task)
    return _entry_of(db, task)


def add_attachments(db: Session, user: User, task_id: str, media: list[UploadedFile]) -> TaskEntry:
    task = _locate(db, task_id)
    _ensure_can_attach(user, task)
    rows = repository.attachments_of(db, task.id)
    _store_media(db, user, task, media, first_position=len(rows))
    db.commit()
    return _entry_of(db, task)


def remove_attachment(db: Session, user: User, task_id: str, attachment_id: str) -> TaskEntry:
    task = _locate(db, task_id)
    _ensure_can_attach(user, task)
    if attachment_id.startswith((LEGACY_ASSIGNMENT_PREFIX, LEGACY_COMPLETION_PREFIX)):
        raise DomainError(messages.LEGACY_ATTACHMENT)
    attachment = repository.find_attachment(db, attachment_id)
    if attachment is None or attachment.personal_task_id != task.id:
        raise DomainError(messages.ATTACHMENT_NOT_FOUND, status=NOT_FOUND)
    # Penerima hanya membuang bukti yang ia unggah sendiri; contoh dari pembuat tugas bukan miliknya.
    if not access.can_edit(user, task.creator_id) and attachment.created_by_id != user.id:
        raise DomainError(messages.NOT_YOURS, status=FORBIDDEN)
    if _done(task) and len(_entry_of(db, task).attachments) <= 1:
        raise DomainError(messages.KEEP_PROOF)

    path = attachment.path
    db.delete(attachment)
    db.commit()
    uploads.discard(db, path)
    return _entry_of(db, task)


def delete(db: Session, user: User, task_id: str) -> None:
    task = _locate(db, task_id)
    if not access.can_delete(user, _done(task), task.assignee_id, task.creator_id):
        raise DomainError(messages.NOT_YOURS, status=FORBIDDEN)
    rows = repository.attachments_of(db, task.id)
    paths = [row.path for row in rows]
    paths += [path for path in (task.assignment_photo_path, task.completion_photo_path) if path]
    for row in rows:
        db.delete(row)
    notices.task_deleted(db, task.id)
    _signal_source(db, task)
    db.delete(task)
    db.commit()
    for path in paths:
        uploads.discard(db, path)


def source_run(db: Session, task_id: str) -> RunContent:
    """Siapa pun yang boleh melihat tugas boleh membaca pengisian yang ditindaklanjutinya, supaya tahu apa yang harus dibereskan."""
    task = _locate(db, task_id)
    content = run_content(db, task.source_run_id) if task.source_run_id else None
    if content is None:
        raise DomainError(messages.SOURCE_GONE, status=NOT_FOUND)
    return content


def attachment_file(db: Session, attachment_id: str) -> tuple[bytes, str]:
    attachment = repository.find_attachment(db, attachment_id)
    stored = uploads.read(db, attachment.path) if attachment is not None else None
    if stored is None:
        raise DomainError(messages.ATTACHMENT_NOT_FOUND, status=NOT_FOUND)
    return stored
