"""HTTP surface of the admin's leave requests; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.models.leave_request import LeaveStatus
from app.models.user import User
from web.management.leave_requests import repository, service
from web.management.leave_requests.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MAX_SEARCH_LENGTH, PERMISSION_MANAGE
from web.management.leave_requests.domain import Decision, LeaveFilter
from web.management.leave_requests.mappers import leave_request_out, leave_request_page_out
from web.management.leave_requests.schemas import DecisionIn, LeaveRequestOut, LeaveRequestPageOut

router = APIRouter(prefix="/leave-requests", tags=["v2-leave-requests-manage"])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("", response_model=LeaveRequestPageOut)
def list_leave_requests(
    leave_status: LeaveStatus | None = Query(None, alias="status", description="Empty means every status"),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Name, username, or words of the reason"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    filter = LeaveFilter(status=leave_status, search=search.strip() if search else None, outlet_id=outlet_id)
    result = service.list_page(db, filter, page, size)
    user = repository.user_by_id(db, {item.user_id for item in result.requests})
    return leave_request_page_out(result, user, public_base_url())


@router.post("/{request_id}/decision", response_model=LeaveRequestOut)
def decide_leave_request(
    request_id: str,
    body: DecisionIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        decided = service.decide(db, admin, request_id, Decision(approve=body.approve, note=body.note))
    user = repository.user_by_id(db, {decided.user_id})[decided.user_id]
    return leave_request_out(decided, user, public_base_url())


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave_request(
    request_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, admin, request_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
