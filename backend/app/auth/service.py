"""Checking a username and password and issuing the token."""
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import attempts, messages
from app.core import messages as core_messages
from app.core.auth import start_session
from app.core.errors import DomainError
from app.core.security import hash_password, verify_password
from app.models.user import User

UNAUTHORIZED = 401
FORBIDDEN = 403
DECOY_PASSWORD = "decoy"


@lru_cache(maxsize=1)
def _decoy_hash() -> str:
    return hash_password(DECOY_PASSWORD)


def login(db: Session, username: str, password: str, channel: str, device_label: str | None) -> tuple[User, str, int]:
    """A wrong username and a wrong password look the same, in the answer and in how long it takes; too many wrong ones lock the username for a while."""
    # Before anything else: a locked username is refused whatever the password, and a name that does not exist is locked the same way.
    attempts.ensure_not_locked(db, attempts.LOGIN, username)
    # A deleted account answers like a username that never existed.
    user = db.scalar(select(User).where(User.username == username, User.deleted_at.is_(None)))
    password_ok = verify_password(password, user.password_hash if user else _decoy_hash())
    if user is None or not password_ok:
        attempts.record_failure(db, attempts.LOGIN, username)
        raise DomainError(messages.INVALID_CREDENTIALS, status=UNAUTHORIZED, code="INVALID_CREDENTIALS")
    # Checked only after the password is right, so a disabled account cannot be found by guessing usernames.
    if not user.is_active:
        raise DomainError(core_messages.ACCOUNT_DISABLED, status=FORBIDDEN, code="ACCOUNT_DISABLED")
    attempts.clear(db, attempts.LOGIN, username)
    token, lifetime = start_session(db, user, channel, device_label)
    return user, token, lifetime
