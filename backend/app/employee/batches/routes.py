"""HTTP surface of batches; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.auth import current_user, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.employee.batches import corrections, messages, service
from app.employee.batches.constants import PERMISSION_VIEW
from app.employee.batches.domain import AnswerDraft
from app.employee.batches.mappers import batch_list_out, batch_out, stored_run_out
from app.employee.batches.schemas import AnswerIn, BatchListOut, BatchOut, StoredRunOut
from app.employee.batches.upload import RULE
from app.models.user import User

router = APIRouter(prefix="/batches", tags=["v2-batches"])

ANSWERS = TypeAdapter(list[AnswerIn])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the app reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


async def _answers(raw: str, sent: list[UploadFile]) -> list[AnswerDraft]:
    """Joins each answer to the photo it points at; only photos are accepted here."""
    try:
        parsed = ANSWERS.validate_json(raw)
    except ValidationError as error:
        raise DomainError(messages.ANSWERS_UNREADABLE) from error
    media = await uploads.receive_all(sent, RULE)
    drafts = []
    for answer in parsed:
        photo = None
        if answer.photo_index is not None:
            if not 0 <= answer.photo_index < len(media):
                raise DomainError(messages.ANSWER_INVALID)
            photo = media[answer.photo_index]
        drafts.append(AnswerDraft(item_id=answer.item_id, value=answer.value, photo=photo, keep_photo=answer.keep_photo))
    return drafts


@router.get("/today", response_model=BatchListOut)
def today_batches(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    return batch_list_out(service.todays_batches(db, user))


@router.post("/{batch_id}/complete", response_model=BatchOut)
async def complete_batch(
    batch_id: str,
    answers: str = Form("[]"),
    sent: list[UploadFile] = File(default=[], alias="files"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    with _domain_errors():
        drafts = await _answers(answers, sent)
        return batch_out(service.complete(db, user, batch_id, drafts))


@router.get("/runs/{run_id}", response_model=StoredRunOut)
def stored_run(run_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Tidak di-cache: dibuka tepat sebelum pengisian diperbaiki, jadi harus isi yang terakhir tersimpan."""
    with _domain_errors():
        entry, answers = corrections.stored(db, user, run_id)
        return stored_run_out(entry, answers, public_base_url())


@router.put("/runs/{run_id}", response_model=BatchOut)
async def fix_run(
    run_id: str,
    answers: str = Form("[]"),
    sent: list[UploadFile] = File(default=[], alias="files"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        drafts = await _answers(answers, sent)
        return batch_out(corrections.fix(db, user, run_id, drafts))


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_run(run_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Batalkan: tugas kembali belum diisi dan isi lamanya tetap tersimpan di Riwayat."""
    with _domain_errors():
        corrections.cancel(db, user, run_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Hapus: pengisian beserta jejak dan fotonya hilang permanen."""
    with _domain_errors():
        corrections.delete(db, user, run_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
