"""HTTP surface of the user screen; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core import bulk
from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.core.http import public_base_url
from app.employee.profile.schemas import PERSONAL_FIELDS
from app.models.user import User
from web.management.users import service
from web.management.users.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, PERMISSION_MANAGE
from web.management.users.domain import UserChanges, UserDraft
from web.management.users.mappers import page_out, user_out
from web.management.users.schemas import UserCreateIn, UserOut, UserPageOut, UserUpdateIn
from app.core.sorting import Sort

router = APIRouter(prefix="/users", tags=["v2-users"])

# Personal fields an admin writes only when sent, so an empty one clears it; the joined date is the admin's alone.
WRITTEN_WHEN_SENT = (*PERSONAL_FIELDS, "joined_date")


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise refusal(error) from error


def _sent(body: UserCreateIn | UserUpdateIn) -> dict:
    return {field: getattr(body, field) for field in WRITTEN_WHEN_SENT if field in body.model_fields_set}


def _draft(body: UserCreateIn) -> UserDraft:
    return UserDraft(
        name=body.name,
        username=body.username,
        password=body.password,
        role_id=body.role_id,
        outlet_id=body.outlet_id,
        personal=_sent(body),
    )


def _changes(body: UserUpdateIn) -> UserChanges:
    return UserChanges(
        name=body.name,
        username=body.username,
        password=body.password,
        role_id=body.role_id,
        outlet_id=body.outlet_id,
        is_active=body.is_active,
        personal=_sent(body),
    )


@router.get("", response_model=UserPageOut)
def list_user(
    search: str | None = Query(None, description="Part of the name, username, phone, email, address, emergency contact, role or branch name"),
    role_id: str | None = Query(None),
    outlet_id: str | None = Depends(readable_outlet_id),
    active: bool | None = Query(None, description="Only active or only inactive accounts"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    viewer: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    return page_out(service.list_user(db, search, role_id, outlet_id, active, sort, page, size), public_base_url(), viewer)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    viewer: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return user_out(service.get(db, viewer, user_id), public_base_url(), viewer)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return user_out(service.create(db, actor, _draft(body)), public_base_url(), actor)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    body: UserUpdateIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return user_out(service.update(db, actor, user_id, _changes(body)), public_base_url(), actor)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, actor, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


bulk.add_bulk_routes(
    router,
    PERMISSION_MANAGE,
    create_schema=UserCreateIn,
    create=lambda db, body, actor, _context: service.create(db, actor, _draft(body)),
    update_schema=UserUpdateIn,
    update=lambda db, user_id, body, actor: service.update(db, actor, user_id, _changes(body)),
    delete=lambda db, user_id, actor: service.delete(db, actor, user_id),
)
