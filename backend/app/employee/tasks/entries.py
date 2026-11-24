"""Builds one task entry with its attachments."""
from collections.abc import Sequence

from app.employee.tasks.constants import LEGACY_ASSIGNMENT_PREFIX, LEGACY_COMPLETION_PREFIX
from app.employee.tasks.domain import AttachmentEntry, FollowUpPlace, SourceRun, TaskEntry
from app.models.task import Task, TaskStatus
from app.models.task_attachment import KIND_PHOTO, TaskAttachment


def attachment_entries(
    rows: Sequence[TaskAttachment], legacy: Sequence[AttachmentEntry] = ()
) -> tuple[AttachmentEntry, ...]:
    """Photos kept in the old single-photo columns come first, then the new attachments in order."""
    current = [AttachmentEntry(id=row.id, kind=row.kind, path=row.path, removable=True) for row in rows]
    return (*legacy, *current)


def _legacy_photos(task: Task) -> list[AttachmentEntry]:
    found = []
    if task.assignment_photo_path:
        found.append(
            AttachmentEntry(LEGACY_ASSIGNMENT_PREFIX + task.id, KIND_PHOTO, task.assignment_photo_path, removable=False)
        )
    if task.completion_photo_path:
        found.append(
            AttachmentEntry(LEGACY_COMPLETION_PREFIX + task.id, KIND_PHOTO, task.completion_photo_path, removable=False)
        )
    return found


def task_entry(
    task: Task, rows: Sequence[TaskAttachment], outlet_name: str | None, source_run: SourceRun | None, follow_up: FollowUpPlace | None
) -> TaskEntry:
    done = task.status == TaskStatus.DONE
    return TaskEntry(
        id=task.id,
        outlet_id=task.outlet_id,
        outlet_name=outlet_name,
        title=task.title,
        description=task.description,
        assignee=task.assignee,
        creator=task.creator,
        completer=task.assignee if done else None,
        due_at=task.due_at,
        done=done,
        completion_note=task.completion_note,
        completed_at=task.completed_at,
        created_at=task.created_at,
        attachments=attachment_entries(rows, _legacy_photos(task)),
        source_run=source_run,
        follow_up=follow_up if source_run else None,
    )

