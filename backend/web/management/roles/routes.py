"""HTTP surface of roles; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache
from app.core.auth import AnyOf, current_user, require_gate, require_permission
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.core.sorting import Sort
from app.models.user import User
from app.employee.schedule.constants import PERMISSION_MANAGE as SCHEDULE_MANAGE
from app.employee.schedule.constants import PERMISSION_VIEW as SCHEDULE_VIEW
from web.management.roles import repository, service
from web.management.roles.constants import PERMISSION_MANAGE
from web.management.roles.domain import RoleChanges, RoleDraft
from web.management.roles.mappers import SORTING, catalog_out, role_out
from web.management.roles.schemas import PermissionOut, RoleCreateIn, RoleOut, RoleStationOut, RoleUpdateIn
from web.management.users.constants import PERMISSION_MANAGE as USER_MANAGE

router = APIRouter(prefix="/roles", tags=["v2-roles"])

ROLES = TypeAdapter(list[RoleOut])
# The user form and the schedule pick a role, so whoever runs them may read the list; nobody else needs it.
ROLE_READERS = AnyOf((PERMISSION_MANAGE, USER_MANAGE, SCHEDULE_VIEW, SCHEDULE_MANAGE))
STATIONS = TypeAdapter(list[RoleStationOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise refusal(error) from error


def _draft(body: RoleCreateIn) -> RoleDraft:
    return RoleDraft(
        name=body.name,
        description=body.description,
        permissions=body.permissions,
        sort_order=body.sort_order,
        is_protected=body.is_protected,
        station_id=body.station_id,
    )


def _changes(body: RoleUpdateIn) -> RoleChanges:
    return RoleChanges(
        name=body.name,
        description=body.description,
        description_given="description" in body.model_fields_set,
        permissions=body.permissions,
        sort_order=body.sort_order,
        is_protected=body.is_protected,
        station_id=body.station_id,
        station_given="station_id" in body.model_fields_set,
    )


@router.get("/permissions", response_model=list[PermissionOut])
def permission_catalog(_: User = Depends(current_user)):
    """Read by every employee: the list is no secret and the profile page explains a person's permissions with it."""
    return catalog_out()


@router.get("/stations", response_model=list[RoleStationOut])
def station_choices(db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Pilihan stasiun pada form peran; di-cache dan ikut berganti saat tabel stations berubah."""
    return cache.read(
        "web.roles.stations",
        (),
        lambda: [RoleStationOut(id=station_id, name=name) for station_id, name in repository.stations(db)],
        STATIONS,
        cache.REFERENCE_SECONDS,
    )


@router.get("", response_model=list[RoleOut])
def list_roles(sort: Sort = None, db: Session = Depends(get_db), viewer: User = Depends(require_gate(ROLE_READERS))):
    """Read by whoever manages roles, user, or the schedule, since their forms pick a role."""
    # Which roles are locked depends on who is looking.
    return cache.read(
        "web.roles",
        (*cache.viewer(viewer), sort),
        lambda: SORTING.apply([role_out(role, viewer) for role in service.list_roles(db)], sort),
        ROLES,
        cache.REFERENCE_SECONDS,
    )


@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: str, db: Session = Depends(get_db), viewer: User = Depends(current_user)):
    with _domain_errors():
        return role_out(service.get(db, role_id), viewer)


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    body: RoleCreateIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return role_out(service.create(db, actor, _draft(body)), actor)


@router.patch("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: str,
    body: RoleUpdateIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return role_out(service.update(db, actor, role_id, _changes(body)), actor)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, actor, role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


bulk.add_bulk_routes(
    router,
    PERMISSION_MANAGE,
    create_schema=RoleCreateIn,
    create=lambda db, body, actor, _context: service.create(db, actor, _draft(body)),
    update_schema=RoleUpdateIn,
    update=lambda db, role_id, body, actor: service.update(db, actor, role_id, _changes(body)),
    delete=lambda db, role_id, actor: service.delete(db, actor, role_id),
)
