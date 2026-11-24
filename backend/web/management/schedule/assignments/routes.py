"""HTTP surface of arranging assignments; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache
from app.core.auth import readable_outlet_id, require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.date_range import Bound
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.models.user import User
from web.management.schedule.assignments import service
from web.management.schedule.assignments.domain import AssignmentChanges, AssignmentDraft
from web.management.schedule.assignments.mappers import assignment_out
from web.management.schedule.assignments.schemas import (
    AssignmentCreateIn,
    AssignmentOut,
    AssignmentSwapIn,
    AssignmentSwapOut,
    AssignmentUpdateIn,
)
from app.employee.schedule.constants import PERMISSION_MANAGE, PERMISSION_VIEW

router = APIRouter(prefix="/schedule/assignments", tags=["v2-schedule"])

ASSIGNMENTS = TypeAdapter(list[AssignmentOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _draft(body: AssignmentCreateIn) -> AssignmentDraft:
    return AssignmentDraft(**body.model_dump())


def _changes(body: AssignmentUpdateIn) -> AssignmentChanges:
    return AssignmentChanges(values=body.model_dump(exclude_unset=True))


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    start: Bound | None = Query(None, description="Defaults to Monday of this week"),
    end: Bound | None = Query(None, description="Defaults to six days after the start"),
    user_id: str | None = Query(None),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """Read by everyone who may view the board, since a cashier needs to know their turn and who works with them."""
    with _domain_errors():
        return cache.read(
            "web.schedule.assignments",
            (start, end, outlet_id, user_id, sort),
            lambda: [assignment_out(item) for item in service.list_assignments(db, start, end, outlet_id, user_id, sort)],
            ASSIGNMENTS,
            cache.LIST_SECONDS,
        )


@router.get("/{schedule_id}", response_model=AssignmentOut)
def get_assignment(
    schedule_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """One assignment, for the page of a single assignment."""
    with _domain_errors():
        return assignment_out(service.get(db, outlet_id, schedule_id))


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    body: AssignmentCreateIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return assignment_out(service.create(db, outlet_id, _draft(body)))


@router.post("/swap", response_model=AssignmentSwapOut)
def swap_assignments(
    body: AssignmentSwapIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        first, second = service.swap(db, user.locked_outlet_id, body.first_id, body.second_id)
    return AssignmentSwapOut(first=assignment_out(first), second=assignment_out(second))


@router.patch("/{schedule_id}", response_model=AssignmentOut)
def update_assignment(
    schedule_id: str,
    body: AssignmentUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return assignment_out(service.update(db, user.locked_outlet_id, schedule_id, _changes(body)))


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    schedule_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, user.locked_outlet_id, schedule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


bulk.add_bulk_routes(
    router,
    PERMISSION_MANAGE,
    create_schema=AssignmentCreateIn,
    create=lambda db, body, _user, outlet_id: service.create(db, outlet_id, _draft(body)),
    create_context=writable_outlet_id,
    update_schema=AssignmentUpdateIn,
    update=lambda db, schedule_id, body, user: service.update(db, user.locked_outlet_id, schedule_id, _changes(body)),
    delete=lambda db, schedule_id, user: service.delete(db, user.locked_outlet_id, schedule_id),
)
