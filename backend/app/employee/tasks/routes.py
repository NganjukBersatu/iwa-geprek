"""HTTP surface of tasks; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache, uploads
from app.core.auth import current_user, readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.http import public_base_url
from app.employee.tasks import service
from app.employee.tasks.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_SEARCH_LENGTH,
    PERMISSION_VIEW,
    STATUS_DONE,
)
from app.employee.tasks.domain import NewTask, TaskChanges
from app.core.file_response import file_response
from app.employee.tasks.mappers import BaseUrls, options_out, page_out, source_run_out, task_out
from app.employee.tasks.upload import RULE
from app.employee.tasks.schemas import CompletionIn, OptionsOut, SourceRunDetailOut, TaskOut, TaskPageOut, TaskUpdateIn
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["v2-tasks"])

OPTIONS = TypeAdapter(OptionsOut)

STATUS_PATTERN = "^(belum|selesai)$"


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the app reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _urls() -> BaseUrls:
    base = public_base_url()
    return BaseUrls(static_base=base, own_base=base)


@router.get("", response_model=TaskPageOut)
def list_tasks(
    task_status: str = Query("belum", alias="status", pattern=STATUS_PATTERN, description="belum or selesai"),
    date_from: date | None = Query(None, description="First day, inclusive; with no date at all the list is this month"),
    date_to: date | None = Query(None, description="Last day, inclusive"),
    q: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Words in the title, the text, or a name"),
    assignee_id: str | None = Query(None, description="Only the tasks given to this person"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    with _domain_errors():
        query = service.task_query(task_status == STATUS_DONE, date_from, date_to, outlet_id, q, assignee_id)
    with _domain_errors():
        return page_out(service.list_tasks(db, user, query, sort, page, size), user, _urls())


@router.get("/mine", response_model=TaskPageOut)
def my_tasks(
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    return page_out(service.my_tasks(db, user, size), user, _urls())


@router.get("/options", response_model=OptionsOut)
def task_options(
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    return cache.read(
        "app.tasks.options",
        (*cache.viewer(user), outlet_id),
        lambda: options_out(service.options(db, user, outlet_id)),
        OPTIONS,
        cache.REFERENCE_SECONDS,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """One task, for the page of a single task."""
    with _domain_errors():
        return task_out(service.get(db, user, str(task_id)), user, _urls())


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    title: str = Form(...),
    description: str | None = Form(None),
    assignee_id: str | None = Form(None),
    due_at: datetime | None = Form(None),
    complete: bool = Form(False),
    source_run_id: str | None = Form(None, max_length=64, description="The outlet or routine task run this task follows up"),
    sent: list[UploadFile] = File(default=[], alias="files"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        media = await uploads.receive_all(sent, RULE)
        data = NewTask(title, description, assignee_id, due_at, complete, source_run_id)
        return task_out(service.create(db, user, data, media), user, _urls())


@router.get("/{task_id}/source-run", response_model=SourceRunDetailOut)
def task_source_run(
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """Tidak di-cache: dibuka sesekali dari rincian tugas dan harus sama dengan yang dilihat admin di Riwayat."""
    with _domain_errors():
        return source_run_out(service.source_run(db, str(task_id)), _urls())


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: UUID,
    body: TaskUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        changes = TaskChanges(body.title, body.description, body.due_at)
        return task_out(service.update(db, user, str(task_id), changes), user, _urls())


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: UUID,
    note: str | None = Form(None),
    sent: list[UploadFile] = File(default=[], alias="files"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        media = await uploads.receive_all(sent, RULE)
        return task_out(service.complete(db, user, str(task_id), note, media), user, _urls())


@router.patch("/{task_id}/completion", response_model=TaskOut)
def fix_completion(
    task_id: UUID,
    body: CompletionIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        return task_out(service.fix_completion(db, user, str(task_id), body.note), user, _urls())


@router.post("/{task_id}/attachments", response_model=TaskOut)
async def add_attachments(
    task_id: UUID,
    sent: list[UploadFile] = File(alias="files"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        media = await uploads.receive_all(sent, RULE)
        return task_out(service.add_attachments(db, user, str(task_id), media), user, _urls())


@router.delete("/{task_id}/attachments/{attachment_id}", response_model=TaskOut)
def remove_attachment(
    task_id: UUID,
    attachment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        return task_out(service.remove_attachment(db, user, str(task_id), attachment_id), user, _urls())


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    with _domain_errors():
        service.delete(db, user, str(task_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/attachments/{attachment_id}/file", include_in_schema=False)
def attachment_file(
    attachment_id: str,
    range_header: str | None = Header(None, alias="Range"),
    db: Session = Depends(get_db),
):
    """Open like the static route: the address holds an id nobody can guess, and a player cannot send a token."""
    with _domain_errors():
        content, content_type = service.attachment_file(db, attachment_id)
    return file_response(content, content_type, range_header)
