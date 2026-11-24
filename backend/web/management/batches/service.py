"""The admin's upkeep of batches."""
import re

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.employee.batches import recurrence
from app.employee.batches.messages import NOT_FOUND
from app.models.outlet_batch import FILL_ONE, KIND_ROUTINE, TARGET_SHIFT, TARGET_USERS, OutletBatch, OutletBatchItem
from app.models.shift_code import ShiftCode
from app.models.user import User
from web.management.batches import messages, repository
from web.management.batches.constants import (
    BATCH_KINDS,
    CLOCK_PATTERN,
    FILL_MODES,
    FOLLOW_UP_STATES,
    REPEAT_UNITS,
    TARGETS,
    ITEM_KINDS,
    MAX_ITEMS,
    MAX_LABEL_LENGTH,
    MAX_NAME_LENGTH,
    NOT_FOUND_STATUS,
)
from web.management.batches.domain import BatchDraft, BatchQuery, CopyOutcome, ItemDraft


def list_batches(db: Session, query: BatchQuery, sort: str | None, page: int, size: int) -> tuple[list[OutletBatch], int]:
    return repository.batch_page(db, query, sort, page, size)


def batch_query(
    outlet_id: str | None,
    kind: str | None,
    search: str | None,
    active: bool | None,
    repeat: str | None,
    fill_mode: str | None,
    shift_code_id: str | None,
) -> BatchQuery:
    """Saringan yang dikirim kosong berarti tidak disaring; nilai yang tidak dikenal ditolak, tidak diabaikan."""
    if repeat and repeat not in REPEAT_UNITS:
        raise DomainError(messages.REPEAT_UNIT_UNKNOWN)
    if fill_mode and fill_mode not in FILL_MODES:
        raise DomainError(messages.FILL_MODE_UNKNOWN)
    return BatchQuery(
        outlet_id=outlet_id,
        kind=wanted_kind(kind),
        search=(search or "").strip() or None,
        active=active,
        repeat_unit=repeat or None,
        fill_mode=fill_mode or None,
        shift_code_id=shift_code_id or None,
    )


def wanted_follow_up(state: str | None) -> str | None:
    """Saringan tindak lanjut; kosong berarti semua, dan nilai yang tidak dikenal ditolak, tidak diabaikan."""
    if not state:
        return None
    if state not in FOLLOW_UP_STATES:
        raise DomainError(messages.FOLLOW_UP_UNKNOWN)
    return state


def wanted_kind(kind: str | None) -> str | None:
    """Jenis yang disaring; kosong berarti kedua jenis, dan jenis yang tidak dikenal ditolak, tidak diabaikan."""
    if not kind:
        return None
    if kind not in BATCH_KINDS:
        raise DomainError(messages.BATCH_KIND_UNKNOWN)
    return kind


def shift_code_options(db: Session, outlet_id: str) -> list[ShiftCode]:
    return repository.working_shift_codes(db, outlet_id)


def get_batch(db: Session, user: User, batch_id: str) -> OutletBatch:
    """One batch for its page; a branch-bound admin never reaches another branch's batch."""
    return _owned_batch(db, user, batch_id)


def create_batch(db: Session, outlet_id: str, draft: BatchDraft) -> OutletBatch:
    if repository.find_outlet(db, outlet_id) is None:
        raise DomainError(messages.BRANCH_UNKNOWN)
    cleaned = _checked_draft(draft)
    batch = OutletBatch(outlet_id=outlet_id, kind=cleaned.kind)
    _apply(batch, cleaned, _shift_codes(db, outlet_id, cleaned), _recipients(db, outlet_id, cleaned))
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def update_batch(db: Session, user: User, batch_id: str, draft: BatchDraft) -> OutletBatch:
    batch = _owned_batch(db, user, batch_id)
    cleaned = _checked_draft(draft)
    if cleaned.kind != batch.kind:
        raise DomainError(messages.BATCH_KIND_FIXED)
    _apply(batch, cleaned, _shift_codes(db, batch.outlet_id, cleaned), _recipients(db, batch.outlet_id, cleaned))
    db.commit()
    db.refresh(batch)
    return batch


def _shift_codes(db: Session, outlet_id: str, draft: BatchDraft) -> list[ShiftCode]:
    """Kode shift tugas rutin wajib kode kerja milik cabang tugas itu; tugas outlet tidak memakai kode shift."""
    if draft.kind != KIND_ROUTINE or draft.target == TARGET_USERS:
        return []
    wanted = set(draft.shift_code_ids)
    if not wanted:
        raise DomainError(messages.SHIFT_CODES_REQUIRED)
    chosen = [code for code in repository.working_shift_codes(db, outlet_id) if code.id in wanted]
    if len(chosen) != len(wanted):
        raise DomainError(messages.SHIFT_CODES_INVALID)
    return chosen


def delete_batch(db: Session, user: User, batch_id: str) -> None:
    db.delete(_owned_batch(db, user, batch_id))
    db.commit()


def _recipients(db: Session, outlet_id: str, draft: BatchDraft) -> list[User]:
    """Orang yang ditunjuk wajib karyawan aktif cabang tugas itu; tugas untuk kode shift tidak menyimpan nama orang."""
    if draft.kind != KIND_ROUTINE or draft.target != TARGET_USERS:
        return []
    wanted = set(draft.user_ids)
    if not wanted:
        raise DomainError(messages.USER_REQUIRED)
    chosen = repository.branch_user_by_ids(db, outlet_id, wanted)
    if len(chosen) != len(wanted):
        raise DomainError(messages.USER_INVALID)
    return chosen


def user_options(db: Session, outlet_id: str, search: str | None, page: int, size: int) -> tuple[list[User], int]:
    return repository.branch_user(db, outlet_id, (search or "").strip() or None, page, size)


def copy_batch(db: Session, user: User, batch_id: str, outlet_ids: list[str]) -> list[CopyOutcome]:
    """Satu salinan per cabang tujuan; tiap cabang lalu memiliki tugasnya sendiri, dan pengulangan tidak membuat salinan ganda."""
    source = _owned_batch(db, user, batch_id)
    wanted = list(dict.fromkeys(outlet_ids))
    if not wanted:
        raise DomainError(messages.COPY_OUTLETS_REQUIRED)
    repository.lock_for_copy(db, source.id)
    outcomes = [_copy_to(db, user, source, outlet_id) for outlet_id in wanted]
    db.commit()
    return outcomes


def _copy_to(db: Session, user: User, source: OutletBatch, outlet_id: str) -> CopyOutcome:
    locked = user.locked_outlet_id
    if locked and outlet_id != locked:
        return CopyOutcome(outlet_id, reason=messages.COPY_NOT_ALLOWED)
    if outlet_id == source.outlet_id:
        return CopyOutcome(outlet_id, reason=messages.COPY_SOURCE_BRANCH)
    if repository.find_outlet(db, outlet_id) is None:
        return CopyOutcome(outlet_id, reason=messages.COPY_BRANCH_UNKNOWN)
    if repository.named_like(db, outlet_id, source.kind, source.name):
        return CopyOutcome(outlet_id, reason=messages.COPY_EXISTS)
    codes = _matching_codes(db, source, outlet_id)
    if codes is None:
        return CopyOutcome(outlet_id, reason=messages.COPY_NO_SHIFT_CODES)
    copy = OutletBatch(
        outlet_id=outlet_id,
        kind=source.kind,
        fill_mode=source.fill_mode,
        target=source.target,
        name=source.name,
        start_clock=source.start_clock,
        end_clock=source.end_clock,
        weekdays=source.weekdays,
        repeat_unit=source.repeat_unit,
        repeat_every=source.repeat_every,
        starts_on=source.starts_on,
        is_active=source.is_active,
        sort_order=source.sort_order,
    )
    copy.items = [OutletBatchItem(label=item.label, kind=item.kind, required=item.required, position=item.position) for item in source.items]
    copy.shift_codes = codes
    db.add(copy)
    db.flush()
    return CopyOutcome(outlet_id, batch_id=copy.id)


def _matching_codes(db: Session, source: OutletBatch, outlet_id: str) -> list[ShiftCode] | None:
    """Kode shift cabang tujuan yang sama dengan milik tugas asal, lewat master atau teks kodenya; None bila ada yang tidak punya padanan."""
    if source.kind != KIND_ROUTINE or source.for_named_user:
        return []
    available = repository.working_shift_codes(db, outlet_id)
    matched = []
    for code in source.shift_codes:
        twin = next((other for other in available if (code.master_id and other.master_id == code.master_id) or other.code == code.code), None)
        if twin is None:
            return None
        matched.append(twin)
    return matched


def _owned_batch(db: Session, user: User, batch_id: str) -> OutletBatch:
    """A branch-bound admin never reaches another branch's batch, even by its id."""
    batch = repository.find_batch(db, batch_id)
    locked = user.locked_outlet_id
    if batch is None or (locked and batch.outlet_id != locked):
        raise DomainError(NOT_FOUND, status=NOT_FOUND_STATUS)
    return batch


def _checked_draft(draft: BatchDraft) -> BatchDraft:
    name = draft.name.strip()[:MAX_NAME_LENGTH]
    if not name:
        raise DomainError(messages.NAME_REQUIRED)
    if not (re.match(CLOCK_PATTERN, draft.start_clock) and re.match(CLOCK_PATTERN, draft.end_clock)):
        raise DomainError(messages.CLOCK_INVALID)
    if draft.start_clock == draft.end_clock:
        raise DomainError(messages.RANGE_EMPTY)
    if not draft.items:
        raise DomainError(messages.ITEMS_REQUIRED)
    if len(draft.items) > MAX_ITEMS:
        raise DomainError(messages.TOO_MANY_ITEMS)
    items = []
    for item in draft.items:
        label = item.label.strip()[:MAX_LABEL_LENGTH]
        if not label:
            raise DomainError(messages.ITEM_LABEL_REQUIRED)
        if item.kind not in ITEM_KINDS:
            raise DomainError(messages.KIND_UNKNOWN)
        items.append(ItemDraft(label=label, kind=item.kind, required=item.required, id=item.id))
    if draft.kind not in BATCH_KINDS:
        raise DomainError(messages.BATCH_KIND_UNKNOWN)
    if draft.fill_mode not in FILL_MODES:
        raise DomainError(messages.FILL_MODE_UNKNOWN)
    if draft.target not in TARGETS:
        raise DomainError(messages.TARGET_UNKNOWN)
    routine = draft.kind == KIND_ROUTINE
    _check_repeat(draft)
    return BatchDraft(
        repeat_unit=draft.repeat_unit,
        repeat_every=draft.repeat_every,
        starts_on=draft.starts_on,
        kind=draft.kind,
        # Tugas outlet selalu cukup diisi satu orang, apa pun yang dikirim.
        fill_mode=draft.fill_mode if routine else FILL_ONE,
        shift_code_ids=tuple(dict.fromkeys(draft.shift_code_ids)) if routine else (),
        # Tugas outlet selalu untuk siapa pun yang hadir, jadi tidak menyimpan penerima.
        target=draft.target if routine else TARGET_SHIFT,
        user_ids=tuple(dict.fromkeys(draft.user_ids)) if routine else (),
        name=name,
        start_clock=draft.start_clock,
        end_clock=draft.end_clock,
        is_active=draft.is_active,
        items=tuple(items),
    )


def _check_repeat(draft: BatchDraft) -> None:
    """Setiap simpanan wajib membawa pola berulang yang lengkap: satuan, angka dalam batas satuannya, dan tanggal mulai."""
    if draft.repeat_unit not in REPEAT_UNITS:
        raise DomainError(messages.REPEAT_UNIT_UNKNOWN)
    limit = recurrence.MAX_EVERY[draft.repeat_unit]
    if not 1 <= draft.repeat_every <= limit:
        raise DomainError(messages.REPEAT_EVERY_INVALID.format(limit=limit))
    if draft.starts_on is None:
        raise DomainError(messages.STARTS_ON_REQUIRED)


def _apply(batch: OutletBatch, draft: BatchDraft, shift_codes: list[ShiftCode], recipients: list[User]) -> None:
    batch.fill_mode = draft.fill_mode
    batch.target = draft.target
    batch.shift_codes = shift_codes
    batch.assigned_user = recipients
    batch.name = draft.name
    batch.start_clock = draft.start_clock
    batch.end_clock = draft.end_clock
    # Templat lama yang disimpan ulang pindah ke pola baru, jadi hari terpilih lamanya dilepas.
    batch.weekdays = None
    batch.repeat_unit = draft.repeat_unit
    batch.repeat_every = draft.repeat_every
    batch.starts_on = draft.starts_on
    batch.is_active = draft.is_active
    existing = {item.id: item for item in batch.items}
    items = []
    for position, drafted in enumerate(draft.items):
        item = existing.pop(drafted.id, None) if drafted.id else None
        if item is None:
            item = OutletBatchItem()
        item.label = drafted.label
        item.kind = drafted.kind
        item.required = drafted.required
        item.position = position
        items.append(item)
    batch.items = items
