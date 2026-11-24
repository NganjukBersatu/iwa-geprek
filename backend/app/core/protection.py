from sqlalchemy import ColumnElement, select

from app.core.errors import DomainError
from app.models.role import Role
from app.models.user import User

FORBIDDEN = 403

ROLE_LOCKED = "Peran {name} hanya bisa diubah oleh pemegang peran itu dan pembuatnya."
ROLE_NOT_GIVEN = "Peran {name} tidak bisa diberikan kepada akun lain."
FULL_ACCESS_GIVER = "Peran {name} hanya bisa diberikan oleh pemegang akses penuh."
ACCOUNT_LOCKED = "Akun {name} hanya bisa diatur oleh pemegang peran {role}."
FULL_ACCESS_ACCOUNT = "Akun {name} hanya bisa diatur oleh pemegang akses penuh."
MARK_LOCKED = "Hanya pemegang peran terlindung yang bisa mengubah tanda terlindung."
UNSCHEDULABLE = "Akun {name} tidak bisa dijadwalkan atau diberi tugas."


def holds(actor: User, role: Role) -> bool:
    return actor.role_id == role.id


def is_protected_account(user: User) -> bool:
    return user.role is not None and bool(user.role.is_protected)


def has_full_access(user: User) -> bool:
    return user.role is not None and user.role.has_full_access


def created(actor: User, role: Role) -> bool:
    return role.created_by is not None and role.created_by == actor.id


def can_use_role(actor: User, role: Role) -> bool:
    """Changing the role itself on the role screen: a protected role only by the accounts holding it and by its creator. Deleting a protected role is refused apart from this."""
    return not role.is_protected or holds(actor, role) or created(actor, role)


def can_give_role(actor: User, role: Role) -> bool:
    """Putting an account in the role: a protected role is never given, and a full-access role only by someone holding full access."""
    if role.is_protected:
        return False
    return not role.has_full_access or has_full_access(actor)


def can_manage_account(actor: User, user: User) -> bool:
    if is_protected_account(user):
        return holds(actor, user.role)
    return not (user.role is not None and user.role.has_full_access) or has_full_access(actor)


def can_mark_protected(actor: User) -> bool:
    return actor.role is not None and bool(actor.role.is_protected)


def ensure_role(actor: User, role: Role) -> None:
    if not can_use_role(actor, role):
        raise DomainError(ROLE_LOCKED.format(name=role.name), status=FORBIDDEN)


def ensure_can_give(actor: User, role: Role) -> None:
    if role.is_protected:
        raise DomainError(ROLE_NOT_GIVEN.format(name=role.name), status=FORBIDDEN)
    if not can_give_role(actor, role):
        raise DomainError(FULL_ACCESS_GIVER.format(name=role.name), status=FORBIDDEN)


def ensure_account(actor: User, user: User) -> None:
    if can_manage_account(actor, user):
        return
    name = user.name or user.username
    if is_protected_account(user):
        raise DomainError(ACCOUNT_LOCKED.format(name=name, role=user.role.name), status=FORBIDDEN)
    raise DomainError(FULL_ACCESS_ACCOUNT.format(name=name), status=FORBIDDEN)


def ensure_can_mark(actor: User) -> None:
    if not can_mark_protected(actor):
        raise DomainError(MARK_LOCKED, status=FORBIDDEN)


def schedulable() -> ColumnElement[bool]:
    return User.role_id.not_in(select(Role.id).where(Role.is_protected.is_(True)))


def ensure_schedulable(user: User) -> None:
    if is_protected_account(user):
        raise DomainError(UNSCHEDULABLE.format(name=user.name or user.username))
