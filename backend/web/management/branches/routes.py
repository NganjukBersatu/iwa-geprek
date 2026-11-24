"""HTTP surface of the branches; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import require_gate, require_permission
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.core.sorting import Sort
from app.models.user import User
from web.management.branches import service
from web.management.branches.constants import PERMISSION_MANAGE, PERMISSION_REMOVE, READ_GATE
from web.management.branches.domain import BranchChanges, BranchDraft
from web.management.branches.mappers import SORTING, branch_out
from web.management.branches.schemas import BranchCreateIn, BranchOut, BranchPeriodIn, BranchReadinessOut, BranchRemovalIn, BranchRemovalOut, BranchUpdateIn

router = APIRouter(prefix="/branches", tags=["v2-branches"])

BRANCHES = TypeAdapter(list[BranchOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise refusal(error) from error


@router.get("", response_model=list[BranchOut])
def list_branches(sort: Sort = None, db: Session = Depends(get_db), admin: User = Depends(require_gate(READ_GATE))):
    return cache.read(
        "web.branches",
        (admin.locked_outlet_id, sort),
        lambda: SORTING.apply([branch_out(outlet) for outlet in service.list_branches(db, admin)], sort),
        BRANCHES,
        cache.REFERENCE_SECONDS,
    )


@router.get("/{outlet_id}", response_model=BranchOut)
def get_branch(outlet_id: str, db: Session = Depends(get_db), admin: User = Depends(require_gate(READ_GATE))):
    """One branch for its detail page; not cached, since it is read once per opening and right after every change."""
    with _domain_errors():
        return branch_out(service.get(db, admin, outlet_id))


# Tidak di-cache: keadaan tablet dan printer berubah dari tablet kapan saja; kartunya dimuat ulang lewat sinyal live.
@router.get("/{outlet_id}/readiness", response_model=BranchReadinessOut)
def branch_readiness(outlet_id: str, db: Session = Depends(get_db), admin: User = Depends(require_gate(READ_GATE))):
    with _domain_errors():
        return service.readiness(db, admin, outlet_id)


@router.post("", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(body: BranchCreateIn, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        return branch_out(service.create(db, BranchDraft(**body.model_dump())))


@router.patch("/{outlet_id}", response_model=BranchOut)
def update_branch(outlet_id: str, body: BranchUpdateIn, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        return branch_out(service.update(db, admin, outlet_id, BranchChanges(values=body.model_dump(exclude_unset=True))))


# Tidak di-cache: tulis; perubahan cabang dan semua tabel yang terhapus dikabarkan lewat live.
@router.post("/{outlet_id}/removal", response_model=BranchRemovalOut)
def remove_branch(outlet_id: str, body: BranchRemovalIn, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_REMOVE))):
    """Deletes a closed branch and everything in it, one bounded step per call; calling again continues where the last one stopped."""
    with _domain_errors():
        progress = service.remove(db, admin, outlet_id, body.name)
    return BranchRemovalOut(done=progress.done, finished_parts=progress.finished_parts, total_parts=progress.total_parts)


@router.put("/{outlet_id}/periods/{original_start}", status_code=status.HTTP_204_NO_CONTENT)
def adjust_period(
    outlet_id: str,
    original_start: date,
    body: BranchPeriodIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Sets one closing period of the branch by hand; neighbours that touched it move along so no day is left without a period."""
    with _domain_errors():
        service.adjust_period(db, admin, outlet_id, original_start, body.start, body.end)


@router.delete("/{outlet_id}/periods/{start}", status_code=status.HTTP_204_NO_CONTENT)
def reset_period(outlet_id: str, start: date, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    """Puts a period set by hand back under the branch rule."""
    with _domain_errors():
        service.reset_period(db, admin, outlet_id, start)
