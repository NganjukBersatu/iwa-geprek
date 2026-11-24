"""HTTP surface of the admin's procedures; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url, sop_media_url
from app.core.sorting import RowSorting, Sort
from app.models.sop import Sop
from app.models.user import User
from web.management.sop import media, service
from web.management.sop.constants import MAX_READER_PAGE_SIZE, PERMISSION_MANAGE, READER_PAGE_SIZE
from web.management.sop.domain import SlideContent, SopContent
from web.management.sop.mappers import draft_out, draft_summary_out, managed_out, managed_summary_out, reader_page_out
from web.management.sop.schemas import (
    DraftIn,
    DraftOut,
    DraftSummaryOut,
    ManagedSopOut,
    ManagedSopSummaryOut,
    ReaderPageOut,
    SopOrderIn,
    SopIn,
    SopMediaOut,
)
from web.management.sop.upload import RULE

router = APIRouter(prefix="/sop", tags=["v2-sop-manage"])
manager = require_permission(PERMISSION_MANAGE)


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _content(body: SopIn) -> SopContent:
    return SopContent(
        title=body.title,
        active=body.active,
        outlet_id=body.outlet_id,
        slides=tuple(SlideContent(title=slide.title, body=slide.body) for slide in body.slides),
    )


def _one(db: Session, user: User, sop: Sop) -> ManagedSopOut:
    return managed_out(sop, service.names_for(db, user, [sop]))


SORTING: RowSorting[ManagedSopSummaryOut] = RowSorting(
    keys={
        "title": lambda row: row.title,
        # A procedure for every branch has no branch name and sorts first.
        "branch": lambda row: row.outlet_name or "",
        "slides": lambda row: row.slide_count,
        "version": lambda row: row.version,
        "status": lambda row: row.active,
        "updated_at": lambda row: row.updated_at,
        # Persentase, supaya SOP cabang kecil dan SOP semua cabang bisa dibandingkan.
        "reads": lambda row: row.read_count / row.audience_count if row.audience_count else 0,
    },
    identity=lambda row: row.id,
)


@router.get("", response_model=list[ManagedSopSummaryOut])
def manage_list(sort: Sort = None, db: Session = Depends(get_db), user: User = Depends(manager)):
    """Without a sort the list comes in the order employees read it, which is where arranging that order starts."""
    sops = service.list_visible(db, user)
    names = service.names_for(db, user, sops)
    return SORTING.apply([managed_summary_out(sop, names) for sop in sops], sort)


@router.get("/drafts", response_model=list[DraftSummaryOut])
def my_drafts(db: Session = Depends(get_db), user: User = Depends(manager)):
    """Only the signed-in person's own drafts; nobody else sees what is still being written."""
    return [draft_summary_out(draft) for draft in service.drafts(db, user)]


@router.get("/drafts/{draft_id}", response_model=DraftOut)
def read_draft(draft_id: str, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        return draft_out(service.read_draft(db, user, draft_id))


@router.put("/drafts", response_model=DraftSummaryOut)
def save_draft(body: DraftIn, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        return draft_summary_out(service.save_draft(db, user, body.id, body.sop_id, body.base_version, body.content))


@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def discard_draft(draft_id: str, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        service.discard_draft(db, user, draft_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/order", response_model=list[ManagedSopSummaryOut])
def reorder(body: SopOrderIn, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        sops = service.reorder(db, user, body.ids)
    names = service.names_for(db, user, sops)
    return [managed_summary_out(sop, names) for sop in sops]


@router.post("/media", response_model=SopMediaOut, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(manager),
):
    """A photo or video for a slide; it comes back as the address to place in the text."""
    with _domain_errors():
        received = await uploads.receive(file, RULE)
        name = media.save(db, received)
    return SopMediaOut(url=sop_media_url(public_base_url(), name), kind=received.kind)


@router.get("/{sop_id}", response_model=ManagedSopOut)
def manage_read(sop_id: str, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        return _one(db, user, service.get(db, user, sop_id))


# Tanpa cache: dibaca ulang lewat sinyal live sop_reads setiap ada karyawan selesai membaca.
@router.get("/{sop_id}/readers", response_model=ReaderPageOut)
def readers(
    sop_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    read: bool | None = Query(None, description="true: read the latest version; false: not yet, or only an older one"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(READER_PAGE_SIZE, ge=1, le=MAX_READER_PAGE_SIZE),
    db: Session = Depends(get_db),
    user: User = Depends(manager),
):
    """Everyone who sees this procedure in the app, those who have not read the latest version first."""
    with _domain_errors():
        return reader_page_out(service.readers(db, user, sop_id, outlet_id, read, sort, page, size))


@router.post("", response_model=ManagedSopOut, status_code=status.HTTP_201_CREATED)
def manage_create(body: SopIn, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        return _one(db, user, service.create(db, user, _content(body), body.draft_id))


@router.put("/{sop_id}", response_model=ManagedSopOut)
def manage_update(sop_id: str, body: SopIn, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        return _one(db, user, service.update(db, user, sop_id, _content(body)))


@router.delete("/{sop_id}", status_code=status.HTTP_204_NO_CONTENT)
def manage_delete(sop_id: str, db: Session = Depends(get_db), user: User = Depends(manager)):
    with _domain_errors():
        service.delete(db, user, sop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
