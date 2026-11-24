"""User accounts: who may sign in, with which role, at which branch; only people trusted with karyawan.kelola issue them."""
import uuid

from sqlalchemy.orm import Session

from app.core import protection, text_rules
from app.core.auth import end_all_sessions
from app.core.clock import now, today
from app.core.errors import DomainError
from app.core.messages import NAME_CHARACTERS
from app.core.password_policy import ensure_acceptable
from app.core.security import hash_password
from app.models.role import FULL_ACCESS_ROLE_IDS, Role
from app.models.user import User
from web.management.users import deletion, messages, repository
from web.management.users.domain import UserChanges, UserDraft, UserPage

NOT_FOUND = 404
FORBIDDEN = 403
CONFLICT = 409


def list_user(
    db: Session, search: str | None, role_id: str | None, outlet_id: str | None, active: bool | None, sort: str | None, page: int, size: int
) -> UserPage:
    rows, total = repository.page_of(db, search, role_id, outlet_id, active, sort, page, size)
    return UserPage(items=rows, total=total, page=page, size=size)


def get(db: Session, actor: User, user_id: str) -> User:
    """One account for its detail page; an account of another branch answers as missing, like in the list."""
    return _user(db, user_id, actor)


def create(db: Session, actor: User, draft: UserDraft) -> User:
    username = draft.username.strip()
    _ensure_plain_name(draft.name.strip())
    _ensure_username_free(db, username)
    role = _role(db, draft.role_id)
    protection.ensure_can_give(actor, role)
    ensure_acceptable(draft.password, username, field="password")
    user = User(
        id=str(uuid.uuid4()),
        name=draft.name.strip(),
        username=username,
        password_hash=hash_password(draft.password),
        role_id=role.id,
        outlet_id=_placement(db, actor, role, draft.outlet_id),
        is_active=True,
        joined_date=today(),
        created_at=now(),
    )
    for field, value in draft.personal.items():
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, actor: User, user_id: str, changes: UserChanges) -> User:
    user = _user(db, user_id, actor)
    protection.ensure_account(actor, user)
    # Demoting oneself out of full access would lose peran.kelola with no way back in.
    demoting = (
        changes.role_id is not None
        and changes.role_id not in FULL_ACCESS_ROLE_IDS
        and user.role_id in FULL_ACCESS_ROLE_IDS
    )
    if user.id == actor.id and (changes.is_active is False or demoting):
        raise DomainError(messages.CANNOT_LOCK_SELF)

    if changes.name is not None:
        if changes.name.strip() != (user.name or ""):
            _ensure_plain_name(changes.name.strip())
        user.name = changes.name.strip()
    if changes.username is not None:
        username = changes.username.strip()
        _ensure_username_free(db, username, except_id=user.id)
        user.username = username
    if changes.password is not None:
        ensure_acceptable(changes.password, user.username, field="password")
        user.password_hash = hash_password(changes.password)
        end_all_sessions(db, user.id)
    # Sending the role an account already has is not giving it, so an owner can still edit their own account.
    if changes.role_id is not None and changes.role_id != user.role_id:
        role = _role(db, changes.role_id)
        protection.ensure_can_give(actor, role)
        user.role_id = role.id
    # Re-checked whenever the role or branch changes, so a promotion releases the branch and a demotion demands one.
    if changes.role_id is not None or changes.outlet_id is not None:
        outlet_id = changes.outlet_id if changes.outlet_id is not None else user.outlet_id
        user.outlet_id = _placement(db, actor, _role(db, user.role_id), outlet_id)
    if changes.is_active is not None:
        user.is_active = changes.is_active
        if not changes.is_active:
            end_all_sessions(db, user.id)
    for field, value in changes.personal.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, actor: User, user_id: str) -> None:
    """The person leaves every list and can no longer sign in; their history stays whole and keeps their name."""
    user = _user(db, user_id, actor)
    protection.ensure_account(actor, user)
    if user.id == actor.id:
        raise DomainError(messages.CANNOT_DELETE_SELF)
    deletion.delete_user(db, user)
    db.commit()


def _user(db: Session, user_id: str, actor: User) -> User:
    user = repository.find(db, user_id)
    # An account of another branch (or one placed at none) answers as missing for someone bound to one branch.
    if user is None or (actor.locked_outlet_id and user.outlet_id != actor.locked_outlet_id):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return user


def _role(db: Session, role_id: str) -> Role:
    role = repository.find_role(db, role_id)
    if role is None:
        raise DomainError(messages.ROLE_NOT_FOUND, status=NOT_FOUND, field="role_id")
    return role


def _ensure_plain_name(name: str) -> None:
    if not text_rules.is_plain_name(name):
        raise DomainError(NAME_CHARACTERS, field="name")


def _ensure_username_free(db: Session, username: str, except_id: str | None = None) -> None:
    owner = repository.username_owner(db, username)
    if owner is not None and owner.id != except_id:
        raise DomainError(messages.USERNAME_TAKEN.format(username=username), status=CONFLICT, field="username")


def _placement(db: Session, actor: User, role: Role, outlet_id: str | None) -> str | None:
    """Full-access roles work across branches; every other role is bound to one, which decides whose drawer their sales enter."""
    if role.has_full_access:
        return None
    # Someone bound to one branch can only place people there; leaving it empty means their own branch.
    if actor.locked_outlet_id:
        if outlet_id and outlet_id != actor.locked_outlet_id:
            raise DomainError(messages.OTHER_BRANCH, status=FORBIDDEN, field="outlet_id")
        outlet_id = actor.locked_outlet_id
    if not outlet_id:
        raise DomainError(messages.BRANCH_REQUIRED, field="outlet_id")
    if not repository.outlet_exists(db, outlet_id):
        raise DomainError(messages.BRANCH_NOT_FOUND, status=NOT_FOUND, field="outlet_id")
    return outlet_id
