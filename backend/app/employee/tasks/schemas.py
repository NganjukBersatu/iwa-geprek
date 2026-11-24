from datetime import date, datetime

from pydantic import BaseModel


class PersonOut(BaseModel):
    id: str
    name: str | None
    username: str
    role_name: str


class OutletOut(BaseModel):
    id: str
    name: str


class AttachmentOut(BaseModel):
    id: str
    kind: str
    url: str
    removable: bool


class SourceRunOut(BaseModel):
    """Pengisian tugas outlet atau rutin yang ditindaklanjuti tugas ini."""

    id: str
    batch_name: str
    kind: str
    day: date


class SourceAnswerOut(BaseModel):
    """Jawaban satu isian; [value] kosong untuk foto, [photo_url] kosong untuk isian selain foto."""

    label: str
    kind: str
    value: str | None
    photo_url: str | None


class SourceRunDetailOut(SourceRunOut):
    """Isi pengisian yang ditindaklanjuti; [problems] menghitung isian yang dijawab Bermasalah."""

    outlet_name: str
    completed_by: str | None
    completed_at: datetime
    problems: int
    answers: list[SourceAnswerOut]


class TaskOut(BaseModel):
    id: str
    status: str
    title: str
    description: str | None
    outlet: OutletOut | None
    assignee: PersonOut | None
    creator: PersonOut | None
    completed_by: PersonOut | None
    due_at: datetime | None
    completion_note: str | None
    completed_at: datetime | None
    created_at: datetime
    attachments: list[AttachmentOut]
    source_run: SourceRunOut | None
    follow_up_number: int | None
    follow_up_total: int | None
    mine: bool
    can_edit: bool
    can_complete: bool
    can_fix: bool
    can_delete: bool


class TaskPageOut(BaseModel):
    items: list[TaskOut]
    total: int
    page: int
    size: int


class OptionsOut(BaseModel):
    outlets: list[OutletOut]
    assignees: list[PersonOut]
    can_manage: bool


class CompletionIn(BaseModel):
    """Catatan selesai yang dibenahi; teks kosong menghapus catatannya."""

    note: str | None = None


class TaskUpdateIn(BaseModel):
    """A field left out stays as it was; an empty description clears it, a deadline cannot be cleared."""

    title: str | None = None
    description: str | None = None
    due_at: datetime | None = None
