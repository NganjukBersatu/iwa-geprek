"""What the batch service receives from the routes."""
from dataclasses import dataclass
from datetime import date

from app.models.outlet_batch import FILL_ONE, KIND_OUTLET, TARGET_SHIFT


@dataclass(frozen=True)
class BatchQuery:
    """Yang menyempitkan daftar templat; yang kosong berarti tidak disaring."""

    outlet_id: str | None = None
    kind: str | None = None
    search: str | None = None
    active: bool | None = None
    repeat_unit: str | None = None
    fill_mode: str | None = None
    shift_code_id: str | None = None


@dataclass(frozen=True)
class RunQuery:
    """Yang menyempitkan riwayat pengisian di dalam rentang harinya."""

    first: date
    last: date
    outlet_id: str | None = None
    kind: str | None = None
    search: str | None = None
    problems: bool | None = None
    batch_id: str | None = None
    follow_up: str | None = None


@dataclass(frozen=True)
class ItemDraft:
    """An existing item keeps its [id] across edits so earlier answers still point at it."""

    label: str
    kind: str
    required: bool
    id: str | None = None


@dataclass(frozen=True)
class BatchDraft:
    name: str
    start_clock: str
    end_clock: str
    is_active: bool
    items: tuple[ItemDraft, ...]
    kind: str = KIND_OUTLET
    fill_mode: str = FILL_ONE
    shift_code_ids: tuple[str, ...] = ()
    repeat_unit: str | None = None
    repeat_every: int = 1
    starts_on: date | None = None
    target: str = TARGET_SHIFT
    user_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CopyOutcome:
    """Hasil menyalin ke satu cabang: tugas barunya, atau alasan cabang itu dilewati."""

    outlet_id: str
    batch_id: str | None = None
    reason: str | None = None
