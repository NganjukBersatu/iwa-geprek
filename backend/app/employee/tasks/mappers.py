"""Turns task entries into response schemas."""
from app.core.http import static_url
from app.employee.tasks import access
from app.employee.tasks.constants import STATUS_DONE, STATUS_OPEN
from app.employee.tasks.domain import AttachmentEntry, TaskEntry, TaskOptions, TaskPage
from app.employee.batches.run_content import RunContent
from app.employee.tasks.schemas import (
    AttachmentOut,
    OptionsOut,
    OutletOut,
    PersonOut,
    SourceAnswerOut,
    SourceRunDetailOut,
    SourceRunOut,
    TaskOut,
    TaskPageOut,
)
from app.models.outlet import Outlet
from app.models.user import User
from app.models.task_attachment import KIND_VIDEO

NO_ROLE = "-"
VIDEO_FILE_PATH = "{base}/v2/tasks/attachments/{id}/file"


class BaseUrls:
    """Photos are served by the shared static route; videos by this service so they carry a playable type."""

    def __init__(self, static_base: str, own_base: str) -> None:
        self.static_base = static_base
        self.own_base = own_base


def person_out(user: User | None) -> PersonOut | None:
    if user is None:
        return None
    return PersonOut(
        id=user.id,
        name=user.name,
        username=user.username,
        role_name=user.role.name if user.role else NO_ROLE,
    )


def outlet_out(outlet: Outlet) -> OutletOut:
    return OutletOut(id=outlet.id, name=outlet.name)


def _attachment_out(item: AttachmentEntry, urls: BaseUrls) -> AttachmentOut:
    if item.kind == KIND_VIDEO:
        url = VIDEO_FILE_PATH.format(base=urls.own_base, id=item.id)
    else:
        url = static_url(urls.static_base, item.path)
    return AttachmentOut(id=item.id, kind=item.kind, url=url, removable=item.removable)


def task_out(entry: TaskEntry, user: User, urls: BaseUrls) -> TaskOut:
    source = entry.source_run
    place = entry.follow_up
    return TaskOut(
        id=entry.id,
        status=STATUS_DONE if entry.done else STATUS_OPEN,
        title=entry.title,
        description=entry.description,
        outlet=OutletOut(id=entry.outlet_id, name=entry.outlet_name) if entry.outlet_id and entry.outlet_name else None,
        assignee=person_out(entry.assignee),
        creator=person_out(entry.creator),
        completed_by=person_out(entry.completer),
        due_at=entry.due_at,
        completion_note=entry.completion_note,
        completed_at=entry.completed_at,
        created_at=entry.created_at,
        attachments=[_attachment_out(item, urls) for item in entry.attachments],
        source_run=SourceRunOut(id=source.id, batch_name=source.batch_name, kind=source.kind, day=source.day) if source else None,
        follow_up_number=place.number if place else None,
        follow_up_total=place.total if place else None,
        mine=entry.assignee_id == user.id,
        can_edit=access.can_edit(user, entry.creator_id),
        can_complete=access.can_complete(user, entry.done, entry.assignee_id),
        can_fix=access.can_fix(user, entry.done, entry.assignee_id),
        can_delete=access.can_delete(user, entry.done, entry.assignee_id, entry.creator_id),
    )


def source_run_out(run: RunContent, urls: BaseUrls) -> SourceRunDetailOut:
    return SourceRunDetailOut(
        id=run.id,
        batch_name=run.batch_name,
        kind=run.kind,
        day=run.day,
        outlet_name=run.outlet_name,
        completed_by=run.completer_name,
        completed_at=run.completed_at,
        problems=run.problems,
        answers=[
            SourceAnswerOut(label=answer.label, kind=answer.kind, value=answer.value, photo_url=static_url(urls.static_base, answer.photo_path))
            for answer in run.answers
        ],
    )


def page_out(page: TaskPage, user: User, urls: BaseUrls) -> TaskPageOut:
    return TaskPageOut(
        items=[task_out(entry, user, urls) for entry in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


def options_out(options: TaskOptions) -> OptionsOut:
    return OptionsOut(
        outlets=[outlet_out(outlet) for outlet in options.outlets],
        assignees=[person_out(user) for user in options.assignees],
        can_manage=options.can_manage,
    )
