"""Memperbaiki atau membatalkan pengisian yang sudah dikirim; isi lamanya selalu disimpan sebagai versi."""
import logging

from sqlalchemy.orm import Session

from app.core import uploads
from app.core.clock import now
from app.core.errors import DomainError
from app.employee.batches import messages, repository, service
from app.employee.batches.domain import AnswerDraft, BatchEntry, StoredAnswer
from app.models.outlet_batch import VERSION_CANCEL, VERSION_DELETE, VERSION_FIX, OutletBatch, OutletBatchAnswer, OutletBatchRun, OutletBatchRunVersion
from app.models.user import User

FORBIDDEN = 403
NOT_FOUND = 404
CONFLICT = 409

log = logging.getLogger(__name__)


def _owned(db: Session, user: User, run: OutletBatchRun | None) -> tuple[OutletBatchRun, OutletBatch]:
    """Pengisian yang sudah dibatalkan diperlakukan seperti tidak ada, karena tugasnya kembali belum diisi."""
    batch = repository.find_batch(db, run.batch_id) if run is not None else None
    if run is None or batch is None or run.cancelled_at is not None:
        raise DomainError(messages.RUN_NOT_FOUND, status=NOT_FOUND)
    if not service.may_fix(user, batch, run):
        raise DomainError(messages.RUN_NOT_YOURS, status=FORBIDDEN)
    return run, batch


def _keep_version(db: Session, run: OutletBatchRun, user: User, action: str, answers: list[OutletBatchAnswer]) -> None:
    db.add(
        OutletBatchRunVersion(
            run_id=run.id,
            number=repository.next_version_number(db, run.id),
            action=action,
            answers=[
                {"item_id": answer.item_id, "label": answer.item_label, "kind": answer.item_kind, "value": answer.value, "photo_path": answer.photo_path}
                for answer in answers
            ],
            completed_by_id=run.completed_by_id,
            completed_at=run.completed_at,
            changed_by_id=user.id,
            changed_at=now(),
        )
    )


def stored(db: Session, user: User, run_id: str) -> tuple[BatchEntry, list[StoredAnswer]]:
    """Pengisian beserta jawabannya, untuk mengisi form perbaikan."""
    run, batch = _owned(db, user, repository.find_run(db, run_id))
    answers = [
        StoredAnswer(item_id=answer.item_id, value=answer.value, photo_path=answer.photo_path)
        for answer in repository.answers_of_run(db, run.id)
        if answer.item_id
    ]
    return service.entry_of(batch, run, user, repository.followed_up(db, [run.id])), answers


def fix(db: Session, user: User, run_id: str, drafts: list[AnswerDraft]) -> BatchEntry:
    """Pengisi dan jam pengisian awal tidak berubah; siapa yang memperbaiki dan kapan tercatat di versinya."""
    run, batch = _owned(db, user, repository.locked_run(db, run_id))
    current = repository.answers_of_run(db, run.id)
    kept_photos = {answer.item_id: answer.photo_path for answer in current if answer.item_id and answer.photo_path}
    filled = service.checked(batch, drafts, kept_photos)
    _keep_version(db, run, user, VERSION_FIX, current)
    for answer in current:
        db.delete(answer)
    db.flush()
    for answer in filled:
        db.add(service.answer_row(db, run, answer))
    db.commit()
    db.refresh(run)
    return service.entry_of(batch, run, user, repository.followed_up(db, [run.id]))


def cancel(db: Session, user: User, run_id: str) -> None:
    """Tugasnya kembali belum diisi; berkas foto lama tidak dihapus karena masih dirujuk versinya."""
    run, _ = _owned(db, user, repository.locked_run(db, run_id))
    if repository.followed_up(db, [run.id]):
        raise DomainError(messages.RUN_HAS_FOLLOW_UP, status=CONFLICT)
    current = repository.answers_of_run(db, run.id)
    _keep_version(db, run, user, VERSION_CANCEL, current)
    for answer in current:
        db.delete(answer)
    run.cancelled_at = now()
    run.cancelled_by_id = user.id
    db.commit()


def delete(db: Session, user: User, run_id: str) -> None:
    """Hapus: jawaban, versi lama, dan fotonya hilang permanen; yang tersisa hanya catatan siapa menghapus dan kapan, supaya admin tetap melihatnya."""
    run = repository.locked_run(db, run_id)
    batch = repository.find_batch(db, run.batch_id) if run is not None else None
    if run is None or batch is None:
        raise DomainError(messages.RUN_NOT_FOUND, status=NOT_FOUND)
    if not service.may_fix(user, batch, run):
        raise DomainError(messages.RUN_NOT_YOURS, status=FORBIDDEN)
    if repository.followed_up(db, [run.id]) and not service.manages(user, batch):
        raise DomainError(messages.RUN_FOLLOWED_NO_DELETE, status=CONFLICT)
    current = repository.answers_of_run(db, run.id)
    paths = [answer.photo_path for answer in current if answer.photo_path] + repository.version_photo_paths(db, run.id)
    number = repository.next_version_number(db, run.id)
    for answer in current:
        db.delete(answer)
    repository.drop_versions(db, run.id)
    db.add(
        OutletBatchRunVersion(
            run_id=run.id, number=number, action=VERSION_DELETE, answers=[], completed_by_id=run.completed_by_id, completed_at=run.completed_at,
            changed_by_id=user.id, changed_at=now(),
        )
    )
    if run.cancelled_at is None:
        run.cancelled_at = now()
        run.cancelled_by_id = user.id
    db.commit()
    for path in set(paths):
        uploads.discard(db, path)
    log.info("outlet batch run deleted", extra={"run_id": run.id, "batch_id": batch.id, "outlet_id": batch.outlet_id, "user_id": user.id})
