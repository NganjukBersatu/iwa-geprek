"""HTTP surface of procedures; every signed-in employee reads the global ones and those of their branch."""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import current_user
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.file_response import file_response
from app.employee.sop import service
from app.employee.sop.mappers import read_out, sop_out, summary_out
from app.employee.sop.schemas import SopOut, SopReadIn, SopReadOut, SopSummaryOut
from app.models.user import User

router = APIRouter(prefix="/sop", tags=["v2-sop"])

SUMMARIES = TypeAdapter(list[SopSummaryOut])
SOP = TypeAdapter(SopOut)


@router.get("", response_model=list[SopSummaryOut])
def list_sop(db: Session = Depends(get_db), user: User = Depends(current_user)):
    def build() -> list[SopSummaryOut]:
        sops = service.list_active(db, user)
        outlets = service.outlet_names(db, sops)
        return [summary_out(sop, outlets) for sop in sops]

    # What is shown depends only on where the person works.
    return cache.read("app.sop", (user.working_outlet_id,), build, SUMMARIES, cache.REFERENCE_SECONDS)


# Tanpa cache: milik satu orang, satu query berindeks user_id.
@router.get("/reads", response_model=list[SopReadOut])
def my_reads(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """The version of each procedure this person last read to the end; the screen marks a higher version as new."""
    return [read_out(read) for read in service.reads(db, user)]


@router.put("/{sop_id}/read", response_model=SopReadOut)
def mark_read(sop_id: str, body: SopReadIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Sent when the last slide is finished; sending it again changes nothing."""
    try:
        return read_out(service.mark_read(db, user, sop_id, body.version))
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("/media/{name}", include_in_schema=False)
def media(name: str, range_header: str | None = Header(None, alias="Range"), db: Session = Depends(get_db)):
    """Open like the static route: the name is an id nobody can guess, and an image or video tag cannot send a token."""
    try:
        content, content_type = service.media_file(db, name)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return file_response(content, content_type, range_header)


@router.get("/{sop_id}", response_model=SopOut)
def read_sop(sop_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    def build() -> SopOut:
        sop = service.get_active(db, user, sop_id)
        return sop_out(sop, service.outlet_names(db, [sop]))

    try:
        return cache.read("app.sop.detail", (user.working_outlet_id, sop_id), build, SOP, cache.REFERENCE_SECONDS)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
