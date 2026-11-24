"""HTTP surface of the branch list the web screens filter by."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import branch_periods, cache
from app.core.auth import current_user
from app.core.clock import today
from app.core.database import get_db
from app.models.user import User
from web.management.outlets import repository
from web.management.outlets.schemas import BranchPeriodOut, OutletOptionOut, OutletPageOut

router = APIRouter(prefix="/outlets", tags=["web-outlets"])

OPTIONS = TypeAdapter(list[OutletOptionOut])
PAGE = TypeAdapter(OutletPageOut)


@router.get("", response_model=list[OutletOptionOut])
def list_outlets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Every branch; a branch-bound account only sees its own."""
    locked = user.locked_outlet_id
    return cache.read(
        "web.outlets", (locked,), lambda: [OutletOptionOut(id=outlet.id, name=outlet.name) for outlet in repository.outlets(db, locked)], OPTIONS, cache.REFERENCE_SECONDS
    )


DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
MAX_SEARCH_LENGTH = 100


@router.get("/search", response_model=OutletPageOut)
def search_outlets(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the branch name or code"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """For pickers that must stay light however many branches exist; a branch-bound account only finds its own."""
    term = (search or "").strip() or None
    locked = user.locked_outlet_id

    def build() -> OutletPageOut:
        rows, total = repository.search(db, locked, term, page, size)
        return OutletPageOut(items=[OutletOptionOut(id=outlet.id, name=outlet.name) for outlet in rows], total=total, page=page, size=size)

    if term:
        return build()
    return cache.read("web.outlets.search", (locked, page, size), build, PAGE, cache.REFERENCE_SECONDS)


@router.get("/periods", response_model=list[BranchPeriodOut])
def list_periods(
    outlet_id: str | None = Query(None, description="One branch; empty means every branch the account may see"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Closing periods already started per branch, the running one first; not cached, since it is a handful of rows read once per branch pick."""
    outlets = repository.outlets(db, user.locked_outlet_id or outlet_id)
    day = today()
    per_branch = branch_periods.listing(db, outlets, day)
    return [
        BranchPeriodOut(outlet_id=outlet.id, outlet_name=outlet.name, start=period.start, end=period.end, adjusted=period.adjusted, sets_pattern=period.sets_pattern, running=period.start <= day <= period.end)
        for outlet in outlets
        for period in per_branch[outlet.id]
    ]
