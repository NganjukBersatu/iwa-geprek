"""HTTP surface of the shift category settings; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.models.user import User
from web.management.shift_categories import service
from web.management.shift_categories.constants import PERMISSION_MANAGE
from web.management.shift_categories.domain import CategoryChanges
from web.management.shift_categories.mappers import category_out
from web.management.shift_categories.schemas import ShiftCategoryOut, ShiftCategoryUpdateIn

router = APIRouter(prefix="/shift-categories", tags=["v2-shift-categories"])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise refusal(error) from error


@router.get("", response_model=list[ShiftCategoryOut])
def list_categories(db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    return [category_out(entry) for entry in service.list_categories(db)]


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        service.delete(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{category_id}", response_model=ShiftCategoryOut)
def update_category(
    category_id: str,
    body: ShiftCategoryUpdateIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    sent = body.model_dump(exclude_unset=True)
    changes = CategoryChanges(
        given=frozenset(sent),
        name=sent.get("name"),
        shift_kind=sent.get("shift_kind"),
        start_from=sent.get("start_from"),
        start_until=sent.get("start_until"),
    )
    with _domain_errors():
        return category_out(service.update(db, admin, category_id, changes))
