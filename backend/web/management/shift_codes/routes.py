"""HTTP surface of shift codes; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache
from app.core.auth import current_user, readable_outlet_id, require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.models.user import User
from web.management.shift_codes import service
from web.management.shift_codes.constants import PERMISSION_MANAGE
from web.management.shift_codes.domain import ShiftCodeChanges, ShiftCodeDraft
from web.management.shift_codes.mappers import shift_code_out
from web.management.shift_codes.schemas import ShiftCodeCreateIn, ShiftCodeOut, ShiftCodeUpdateIn

router = APIRouter(prefix="/shift-codes", tags=["v2-shift-codes"])

CODES = TypeAdapter(list[ShiftCodeOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise refusal(error) from error


def _draft(body: ShiftCodeCreateIn) -> ShiftCodeDraft:
    return ShiftCodeDraft(**body.model_dump())


def _changes(body: ShiftCodeUpdateIn) -> ShiftCodeChanges:
    values = body.model_dump(exclude_unset=True)
    return ShiftCodeChanges(values=values, crosses_midnight=values.pop("crosses_midnight", None))


@router.get("", response_model=list[ShiftCodeOut])
def list_codes(
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    """Read by every employee, since everyone sees the schedule board."""
    return cache.read(
        "web.shift-codes", (outlet_id,), lambda: [shift_code_out(code) for code in service.list_codes(db, outlet_id)], CODES, cache.REFERENCE_SECONDS
    )


@router.post("", response_model=ShiftCodeOut, status_code=status.HTTP_201_CREATED)
def create_code(
    body: ShiftCodeCreateIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return shift_code_out(service.create(db, outlet_id, _draft(body)))


@router.patch("/{code_id}", response_model=ShiftCodeOut)
def update_code(
    code_id: str,
    body: ShiftCodeUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return shift_code_out(service.update(db, user, code_id, _changes(body)))


@router.delete("/{code_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_code(
    code_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, user, code_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


bulk.add_bulk_routes(
    router,
    PERMISSION_MANAGE,
    create_schema=ShiftCodeCreateIn,
    create=lambda db, body, _user, outlet_id: service.create(db, outlet_id, _draft(body)),
    create_context=writable_outlet_id,
    update_schema=ShiftCodeUpdateIn,
    update=lambda db, code_id, body, user: service.update(db, user, code_id, _changes(body)),
    delete=lambda db, code_id, user: service.delete(db, user, code_id),
)
