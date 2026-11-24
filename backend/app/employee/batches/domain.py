"""What the batch service hands to the mappers and receives from the routes."""
from dataclasses import dataclass
from datetime import datetime

from app.core.uploads import UploadedFile
from app.models.outlet_batch import OutletBatch, OutletBatchItem


@dataclass(frozen=True)
class AnswerDraft:
    item_id: str
    value: str | None
    photo: UploadedFile | None
    # Foto yang sudah tersimpan dipertahankan saat pengisian diperbaiki tanpa mengunggah ulang.
    keep_photo: bool = False


@dataclass(frozen=True)
class Filled:
    """Jawaban yang sudah diperiksa; [photo_path] terisi bila foto lama dipertahankan."""

    item: OutletBatchItem
    value: str | None
    photo: UploadedFile | None
    photo_path: str | None = None


@dataclass(frozen=True)
class StoredAnswer:
    """Jawaban yang tersimpan, untuk mengisi form perbaikan."""

    item_id: str
    value: str | None
    photo_path: str | None


@dataclass(frozen=True)
class BatchEntry:
    """A batch as one person sees it today: still to fill, or already filled by someone."""

    batch: OutletBatch
    completed_at: datetime | None
    completed_by: str | None
    run_id: str | None = None
    can_fix: bool = False
    can_cancel: bool = False
    can_delete: bool = False

    @property
    def completed(self) -> bool:
        return self.completed_at is not None
