"""Today's batches for a person and finishing one."""
import math
import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.clock import WIB, as_aware, now, today
from app.core.errors import DomainError
from app.core.uploads import UploadedFile
from app.employee.batches import messages, repository
from app.employee.batches.constants import (
    CLOCK_SEPARATOR,
    KIND_NUMBER,
    KIND_PHOTO,
    KIND_TOGGLE,
    MAX_TEXT_LENGTH,
    MEDIA_FOLDER,
    PERMISSION_MANAGE,
    TOGGLE_VALUES,
)
from app.employee.batches.domain import AnswerDraft, BatchEntry, Filled
from app.employee.batches.recurrence import applies_on
from app.employee.batches.upload import RULE
from app.models.attendance import Attendance
from app.models.outlet_batch import KIND_ROUTINE, OutletBatch, OutletBatchAnswer, OutletBatchItem, OutletBatchRun
from app.models.user import User

FORBIDDEN = 403
NOT_FOUND = 404
DECIMAL_COMMA = ","
DECIMAL_POINT = "."


def window_of(batch: OutletBatch, day: date) -> tuple[datetime, datetime]:
    """The batch's range on [day]; an end that is not after the start means the range runs past midnight."""
    start = datetime.combine(day, _clock(batch.start_clock), tzinfo=WIB)
    end = datetime.combine(day, _clock(batch.end_clock), tzinfo=WIB)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def todays_batches(db: Session, user: User) -> list[BatchEntry]:
    """Batches of the branches where this person has clocked in today and was there during the batch's range."""
    day = today()
    attendances = repository.attendances_of(db, user.id, day)
    if not attendances:
        return []
    current = now()
    outlet_ids = {attendance.outlet_id for attendance in attendances}
    scheduled = repository.scheduled_shift_codes(db, user.id, day)
    candidates = [
        batch
        for batch in repository.active_batches(db, outlet_ids)
        if applies_on(batch, day) and _assigned(batch, user.id, scheduled) and _present_in(attendances, batch.outlet_id, window_of(batch, day), current)
    ]
    runs = repository.runs_of(db, [batch.id for batch in candidates], day, user.id)
    followed = repository.followed_up(db, [run.id for run in runs.values()])
    return [entry_of(batch, runs.get(batch.id), user, followed) for batch in candidates]


def complete(db: Session, user: User, batch_id: str, answers: list[AnswerDraft]) -> BatchEntry:
    """Diisi sekaligus oleh satu orang; item wajib yang kosong menolak pengiriman dan menyebut yang kurang."""
    batch = repository.find_batch(db, batch_id)
    if batch is None or not batch.is_active:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    entry = next((item for item in todays_batches(db, user) if item.batch.id == batch.id), None)
    if entry is None:
        raise DomainError(messages.ROUTINE_NOT_AVAILABLE if batch.kind == KIND_ROUTINE else messages.NOT_AVAILABLE, status=FORBIDDEN)
    if entry.completed:
        raise DomainError(messages.ALREADY_DONE)

    filled = checked(batch, answers)
    run = repository.cancelled_run(db, batch.id, today(), batch.filler_key(user.id))
    if run is not None:
        run.completed_by_id = user.id
        run.completed_at = now()
        run.cancelled_at = None
        run.cancelled_by_id = None
    else:
        run = OutletBatchRun(batch_id=batch.id, day=today(), completed_by_id=user.id, filler_key=batch.filler_key(user.id))
        db.add(run)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise DomainError(messages.ALREADY_DONE) from error
    for answer in filled:
        db.add(answer_row(db, run, answer))
    db.commit()
    db.refresh(run)
    return entry_of(batch, run, user, set())


def _clock(text: str) -> time:
    hour, minute = text.split(CLOCK_SEPARATOR)
    return time(int(hour), int(minute))


def _assigned(batch: OutletBatch, user_id: str, scheduled: set[str]) -> bool:
    """Tugas outlet untuk siapa pun yang hadir; tugas rutin untuk orang yang ditunjuk, atau yang dijadwalkan di salah satu kode shiftnya hari ini."""
    if batch.kind != KIND_ROUTINE:
        return True
    if batch.for_named_user:
        return any(person.id == user_id for person in batch.recipients)
    return any(code.id in scheduled for code in batch.shift_codes)


def _present_in(attendances: list[Attendance], outlet_id: str, window: tuple[datetime, datetime], current: datetime) -> bool:
    for attendance in attendances:
        if attendance.outlet_id != outlet_id or attendance.clock_in_at is None:
            continue
        left = as_aware(attendance.clock_out_at) if attendance.clock_out_at else current
        if as_aware(attendance.clock_in_at) < window[1] and left > window[0]:
            return True
    return False


def manages(user: User, batch: OutletBatch) -> bool:
    """Pengelola tugas yang boleh mengurus cabang tugas itu."""
    locked = user.locked_outlet_id
    return user.allows(PERMISSION_MANAGE) and (not locked or locked == batch.outlet_id)


def may_fix(user: User, batch: OutletBatch, run: OutletBatchRun) -> bool:
    """Pengisinya sendiri, atau pengelola tugas cabang itu."""
    return run.completed_by_id == user.id or manages(user, batch)


def entry_of(batch: OutletBatch, run: OutletBatchRun | None, user: User, followed: set[str]) -> BatchEntry:
    """[followed] berisi pengisian yang sudah ditindaklanjuti; pengisian seperti itu hanya boleh diperbaiki, tidak dibatalkan."""
    if run is None or run.cancelled_at is not None:
        return BatchEntry(batch=batch, completed_at=None, completed_by=None)
    completer = run.completer
    name = (completer.name or completer.username) if completer is not None else None
    fixable = may_fix(user, batch, run)
    untouched = run.id not in followed
    return BatchEntry(
        batch=batch,
        completed_at=run.completed_at,
        completed_by=name,
        run_id=run.id,
        can_fix=fixable,
        can_cancel=fixable and untouched,
        # Pengisian yang sudah ditindaklanjuti hanya dihapus pengelola, supaya tugas tindak lanjutnya tidak kehilangan asalnya tanpa sepengetahuan admin.
        can_delete=fixable and (untouched or manages(user, batch)),
    )


def checked(batch: OutletBatch, answers: list[AnswerDraft], kept_photos: dict[str, str] | None = None) -> list[Filled]:
    """[kept_photos] memetakan isian ke foto yang sudah tersimpan, untuk jawaban yang meminta fotonya dipertahankan."""
    kept_photos = kept_photos or {}
    by_item = {answer.item_id: answer for answer in answers}
    if len(by_item) != len(answers) or not set(by_item) <= {item.id for item in batch.items}:
        raise DomainError(messages.ANSWER_INVALID)
    missing: list[str] = []
    filled: list[Filled] = []
    for item in batch.items:
        draft = by_item.get(item.id)
        value, photo = _read(item, draft)
        keeps = draft is not None and draft.keep_photo and photo is None and item.kind == KIND_PHOTO
        path = kept_photos.get(item.id) if keeps else None
        if value is None and photo is None and path is None:
            if item.required:
                missing.append(item.label)
            continue
        filled.append(Filled(item=item, value=value, photo=photo, photo_path=path))
    if missing:
        raise DomainError(messages.MISSING_REQUIRED.format(labels=", ".join(missing)))
    return filled


def _read(item: OutletBatchItem, answer: AnswerDraft | None) -> tuple[str | None, UploadedFile | None]:
    """An empty answer is None; a filled one is checked against what the item asks for."""
    if answer is None:
        return None, None
    if item.kind == KIND_PHOTO:
        return None, answer.photo
    text = (answer.value or "").strip()
    if not text:
        return None, None
    if item.kind == KIND_TOGGLE:
        if text not in TOGGLE_VALUES:
            raise DomainError(messages.ANSWER_INVALID)
        return text, None
    if item.kind == KIND_NUMBER:
        number = text.replace(DECIMAL_COMMA, DECIMAL_POINT)
        try:
            parsed = float(number)
        except ValueError as error:
            raise DomainError(messages.ANSWER_INVALID) from error
        if not math.isfinite(parsed):
            raise DomainError(messages.ANSWER_INVALID)
        return number, None
    return text[:MAX_TEXT_LENGTH], None


def answer_row(db: Session, run: OutletBatchRun, filled: Filled) -> OutletBatchAnswer:
    answer_id = str(uuid.uuid4())
    path = filled.photo_path
    if filled.photo is not None:
        path = f"{MEDIA_FOLDER}/{run.id}/{answer_id}{filled.photo.extension}"
        uploads.store(db, path, filled.photo, RULE)
    item = filled.item
    return OutletBatchAnswer(
        id=answer_id, run_id=run.id, item_id=item.id, item_label=item.label, item_kind=item.kind, value=filled.value, photo_path=path
    )
