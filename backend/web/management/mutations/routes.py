"""HTTP surface of the mutation screen; read only."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.models.user import User
from web.management.mutations import service
from web.management.mutations.schemas import MutationDetailOut, MutationPageOut

router = APIRouter(prefix="/mutations", tags=["web-mutations"])

PAGE = TypeAdapter(MutationPageOut)
DETAIL = TypeAdapter(MutationDetailOut)

PERMISSION_VIEW = "mutasi.lihat"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@router.get("", response_model=MutationPageOut)
def list_mutations(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    try:
        return cache.read(
            "web.mutations",
            (start, end, outlet_id, sort, page, size),
            lambda: service.page(db, start, end, outlet_id, sort, page, size),
            PAGE,
            cache.LIST_SECONDS,
        )
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("/{session_id}", response_model=MutationDetailOut)
def mutation_detail(
    session_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    try:
        return cache.read(
            "web.mutations.detail",
            (session_id, outlet_id),
            lambda: service.detail(db, session_id, outlet_id),
            DETAIL,
            cache.LIST_SECONDS,
        )
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
