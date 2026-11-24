from datetime import datetime

from pydantic import BaseModel


class ItemOut(BaseModel):
    id: str
    label: str
    kind: str
    required: bool
    position: int


class BatchOut(BaseModel):
    """Tugas outlet atau tugas rutin seperti yang dilihat satu orang hari ini; [completed] pada tugas yang diisi tiap orang berarti pengisiannya sendiri."""

    id: str
    kind: str
    fill_mode: str
    name: str
    start_clock: str
    end_clock: str
    completed: bool
    completed_at: datetime | None
    completed_by: str | None
    run_id: str | None
    can_fix: bool
    can_cancel: bool
    can_delete: bool
    items: list[ItemOut]


class BatchListOut(BaseModel):
    items: list[BatchOut]


class AnswerIn(BaseModel):
    """[photo_index] points at the position of the photo among the uploaded files."""

    item_id: str
    value: str | None = None
    photo_index: int | None = None
    keep_photo: bool = False


class StoredAnswerOut(BaseModel):
    item_id: str
    value: str | None
    photo_url: str | None


class StoredRunOut(BaseModel):
    """Pengisian yang akan diperbaiki: tugasnya beserta jawaban yang tersimpan."""

    batch: BatchOut
    answers: list[StoredAnswerOut]
