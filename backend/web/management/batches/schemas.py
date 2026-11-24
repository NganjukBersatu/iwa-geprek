from datetime import date, datetime

from pydantic import BaseModel, Field

from app.employee.batches.schemas import ItemOut
from app.models.outlet_batch import FILL_ONE, KIND_OUTLET, TARGET_SHIFT
from web.management.batches.constants import MAX_ITEMS, MAX_LABEL_LENGTH, MAX_COPY_OUTLETS, MAX_NAME_LENGTH, MAX_RECIPIENTS, MAX_SHIFT_CODES


class BatchShiftCodeOut(BaseModel):
    """Kode shift satu cabang yang bisa diberi tugas rutin."""

    id: str
    code: str
    color: str | None
    start_clock: str | None
    end_clock: str | None


class BatchShiftCodeListOut(BaseModel):
    items: list[BatchShiftCodeOut]


class BatchUserOut(BaseModel):
    """Karyawan yang bisa atau sudah ditunjuk menerima tugas rutin."""

    id: str
    name: str
    role_name: str | None


class BatchUserPageOut(BaseModel):
    items: list[BatchUserOut]
    total: int
    page: int
    size: int


class BatchCopyIn(BaseModel):
    batch_id: str
    outlet_ids: list[str] = Field(max_length=MAX_COPY_OUTLETS)


class BatchCopyCreatedOut(BaseModel):
    outlet_id: str
    outlet_name: str
    batch_id: str


class BatchCopySkippedOut(BaseModel):
    outlet_id: str
    outlet_name: str
    reason: str


class BatchCopyOut(BaseModel):
    """Hasil per cabang: yang dibuat dan yang dilewati beserta alasannya."""

    created: list[BatchCopyCreatedOut]
    skipped: list[BatchCopySkippedOut]


class ManagedBatchOut(BaseModel):
    """Templat seperti yang disunting admin; [repeat_unit] kosong hanya pada templat lama yang masih berulang menurut [weekdays] (kosong berarti tiap hari), dan [shift_codes] hanya terisi untuk tugas rutin."""

    id: str
    outlet_id: str
    outlet_name: str
    kind: str
    fill_mode: str
    shift_codes: list[BatchShiftCodeOut]
    target: str
    user: list[BatchUserOut]
    name: str
    start_clock: str
    end_clock: str
    repeat_unit: str | None
    repeat_every: int
    starts_on: date | None
    weekdays: list[int]
    is_active: bool
    items: list[ItemOut]


class ManagedBatchListOut(BaseModel):
    items: list[ManagedBatchOut]
    total: int
    page: int
    size: int


class RunOut(BaseModel):
    """Satu pengisian tugas outlet; [problems] menghitung isian yang dijawab Bermasalah."""

    id: str
    kind: str
    day: date
    completed_at: datetime
    batch_name: str
    outlet_id: str
    outlet_name: str
    completed_by: str | None
    problems: int
    follow_up_total: int
    follow_up_open: int
    cancelled: bool
    version_count: int
    fixed_by: str | None
    fixed_at: datetime | None
    last_action: str | None


class FollowUpOut(BaseModel):
    """Tugas karyawan yang menindaklanjuti satu pengisian."""

    task_id: str
    number: int
    title: str
    assignee_name: str | None
    done: bool
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class RunPageOut(BaseModel):
    items: list[RunOut]
    total: int
    page: int
    size: int


class AnswerOut(BaseModel):
    """Jawaban satu isian; [value] kosong untuk foto, [photo_url] kosong untuk isian selain foto."""

    label: str
    kind: str
    value: str | None
    photo_url: str | None


class RunVersionOut(BaseModel):
    """Isi pengisian sebelum satu perbaikan (fix) atau pembatalan (cancel); penghapusan (delete) tercatat tanpa isi."""

    number: int
    action: str
    changed_by: str | None
    changed_at: datetime
    completed_by: str | None
    completed_at: datetime
    answers: list[AnswerOut]


class RunDetailOut(RunOut):
    answers: list[AnswerOut]
    follow_ups: list[FollowUpOut]
    versions: list[RunVersionOut]


class ItemIn(BaseModel):
    id: str | None = None
    label: str = Field(max_length=MAX_LABEL_LENGTH)
    kind: str
    required: bool = True


class BatchIn(BaseModel):
    kind: str = KIND_OUTLET
    fill_mode: str = FILL_ONE
    shift_code_ids: list[str] = Field(default_factory=list, max_length=MAX_SHIFT_CODES)
    target: str = TARGET_SHIFT
    user_ids: list[str] = Field(default_factory=list, max_length=MAX_RECIPIENTS)
    name: str = Field(max_length=MAX_NAME_LENGTH)
    start_clock: str
    end_clock: str
    repeat_unit: str
    repeat_every: int = 1
    starts_on: date
    is_active: bool = True
    items: list[ItemIn] = Field(max_length=MAX_ITEMS)
