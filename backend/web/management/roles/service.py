"""Roles and their permissions; the owner decides who may do what, the code only guards the full-access roles."""
import uuid

from sqlalchemy.orm import Session

from app.core import protection, text_rules
from app.core.clock import now
from app.core.errors import DomainError
from app.core.messages import NAME_CHARACTERS
from app.models.role import Role
from app.models.user import User
from web.management.roles import messages, repository
from app.core.permissions.registry import ALL_KEYS
from web.management.roles.domain import RoleChanges, RoleDraft

NOT_FOUND = 404
CONFLICT = 409


def known_permissions(keys) -> list[str]:
    """Drops unknown keys instead of rejecting them, so a role holding a key removed from the catalog can still be saved."""
    return sorted({key for key in keys if key in ALL_KEYS})


def effective_permissions(role: Role) -> list[str]:
    """A full-access role is read from the catalog, so a permission added later is already theirs."""
    if role.has_full_access:
        return sorted(ALL_KEYS)
    return sorted({key for key in (role.permissions or []) if isinstance(key, str) and key in ALL_KEYS})


def _ensure_plain_name(name: str) -> None:
    if not text_rules.is_plain_name(name):
        raise DomainError(NAME_CHARACTERS, field="name")


def list_roles(db: Session) -> list[Role]:
    return repository.all_roles(db)


def get(db: Session, role_id: str) -> Role:
    """One role for its page; read by every employee, like the list."""
    return _role(db, role_id)


def create(db: Session, actor: User, draft: RoleDraft) -> Role:
    if draft.is_protected:
        protection.ensure_can_mark(actor)
    name = draft.name.strip()
    _ensure_plain_name(name)
    if repository.name_taken(db, name):
        raise DomainError(messages.NAME_TAKEN.format(name=name), status=CONFLICT, field="name")
    current = now()
    role = Role(
        id=str(uuid.uuid4()),
        name=name,
        description=_description(draft.description),
        permissions=known_permissions(draft.permissions),
        is_default=False,
        sort_order=draft.sort_order,
        is_protected=draft.is_protected,
        station_id=_station(db, draft.station_id),
        created_by=actor.id,
        created_at=current,
        updated_at=current,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update(db: Session, actor: User, role_id: str, changes: RoleChanges) -> Role:
    role = _role(db, role_id)
    protection.ensure_role(actor, role)
    if changes.is_protected is not None:
        protection.ensure_can_mark(actor)
    if role.has_full_access and changes.permissions is not None:
        raise DomainError(messages.FULL_ACCESS_LOCKED.format(name=role.name))
    if changes.name:
        name = changes.name.strip()
        if name != role.name:
            _ensure_plain_name(name)
        if repository.name_taken(db, name, except_id=role.id):
            raise DomainError(messages.NAME_TAKEN.format(name=name), status=CONFLICT, field="name")
        role.name = name
    if changes.description_given:
        role.description = _description(changes.description)
    if changes.permissions is not None:
        role.permissions = known_permissions(changes.permissions)
    if changes.sort_order is not None:
        role.sort_order = changes.sort_order
    if changes.is_protected is not None:
        role.is_protected = changes.is_protected
    if changes.station_given:
        role.station_id = _station(db, changes.station_id)
    role.updated_at = now()
    db.commit()
    db.refresh(role)
    return role


def delete(db: Session, actor: User, role_id: str) -> None:
    role = _role(db, role_id)
    protection.ensure_role(actor, role)
    if role.is_default:
        raise DomainError(messages.DEFAULT_UNDELETABLE.format(name=role.name))
    if role.is_protected:
        raise DomainError(messages.PROTECTED_UNDELETABLE.format(name=role.name))
    # Counted here rather than left to the foreign key, so the owner learns how many people to move first.
    assigned = repository.user_count(db, role.id)
    if assigned:
        raise DomainError(messages.STILL_ASSIGNED.format(count=assigned))
    db.delete(role)
    db.commit()


def _role(db: Session, role_id: str) -> Role:
    role = repository.find(db, role_id)
    if role is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return role


def _station(db: Session, station_id: str | None) -> str | None:
    """Kosong berarti tanpa stasiun; id yang tidak ada ditolak dengan pesan, bukan dibiarkan jatuh di foreign key."""
    if station_id is None:
        return None
    if not repository.station_exists(db, station_id):
        raise DomainError(messages.STATION_NOT_FOUND, field="station_id")
    return station_id


def _description(text: str | None) -> str | None:
    return (text or "").strip() or None
