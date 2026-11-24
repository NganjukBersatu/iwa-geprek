"""Slows down guessing: a subject that collects too many wrong attempts is locked for a while, longer each time.

Two rules use it: wrong passwords per username (sign-in) and wrong pairing codes for the whole system (a tablet that is not paired yet has no
account to count against, and the address of the caller cannot be trusted behind the hosting proxy).
"""
import hashlib
import math
from dataclasses import dataclass
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import case, delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.auth import messages
from app.core.clock import now
from app.core.errors import CodedHTTPException, DomainError
from app.models.login_attempt import LoginAttempt

TOO_MANY_REQUESTS = 429
SECONDS_PER_MINUTE = 60

# A day without a wrong attempt starts the escalation over.
QUIET_PERIOD = timedelta(days=1)
# Rows untouched for this long (and not locked) are removed, a few at a time, whenever a wrong attempt is recorded.
RETENTION = timedelta(days=1)
CLEANUP_BATCH = 50

_TABLE = LoginAttempt.__table__


@dataclass(frozen=True)
class Rule:
    scope: str
    # Wrong attempts allowed inside the window before the subject is locked.
    max_failures: int
    window: timedelta
    # The first lock lasts this long; every lock in a row doubles it, up to the cap.
    first_lock: timedelta
    longest_lock: timedelta
    message: str
    # The stable code of the refusal, which a client turns into its own sentence.
    code: str


LOGIN = Rule("login", 10, timedelta(minutes=15), timedelta(minutes=15), timedelta(hours=4), messages.TOO_MANY_ATTEMPTS, "TOO_MANY_LOGIN_ATTEMPTS")
PAIRING = Rule("pairing", 20, timedelta(minutes=15), timedelta(minutes=15), timedelta(hours=1), messages.TOO_MANY_PAIRING_ATTEMPTS, "TOO_MANY_PAIRING_ATTEMPTS")
# The pairing code is not tied to anyone, so every wrong code counts against this one subject.
PAIRING_SUBJECT = "all"


class AttemptsLocked(DomainError):
    """Too many wrong attempts; `retry_after` is the wait in seconds, sent to the client as Retry-After."""

    def __init__(self, rule: Rule, seconds: int) -> None:
        super().__init__(
            rule.message.format(minutes=max(1, math.ceil(seconds / SECONDS_PER_MINUTE))), status=TOO_MANY_REQUESTS, code=rule.code
        )
        self.retry_after = max(1, seconds)


def refusal(error: DomainError) -> HTTPException:
    """A locked subject also tells the client how long to wait, in the standard header."""
    headers = {"Retry-After": str(error.retry_after)} if isinstance(error, AttemptsLocked) else None
    return CodedHTTPException(error.status, error.message, code=error.code, headers=headers)


def _key(rule: Rule, subject: str) -> str:
    """The SHA-256 of the scope and the lower-cased subject: nothing typed is stored, and a name that does not exist counts like one that does."""
    return hashlib.sha256(f"{rule.scope}:{' '.join(subject.split()).lower()}".encode("utf-8")).hexdigest()


def ensure_not_locked(db: Session, rule: Rule, subject: str) -> None:
    """Refuses before the secret is looked at, so a locked subject learns nothing from further guesses."""
    locked_until = db.scalar(select(LoginAttempt.locked_until).where(LoginAttempt.username_hash == _key(rule, subject)))
    moment = now()
    if locked_until is not None and locked_until > moment:
        raise AttemptsLocked(rule, math.ceil((locked_until - moment).total_seconds()))


def record_failure(db: Session, rule: Rule, subject: str) -> None:
    """Counts one wrong attempt and commits; the count and the lock are decided inside the database, so parallel guesses cannot slip through."""
    key = _key(rule, subject)
    moment = now()
    window_over = _TABLE.c.window_started_at < moment - rule.window
    # Every expression below reads the row as it was before this statement.
    counted = (
        insert(LoginAttempt)
        .values(username_hash=key, failures=1, lockouts=0, window_started_at=moment, locked_until=None, updated_at=moment)
        .on_conflict_do_update(
            index_elements=[_TABLE.c.username_hash],
            set_={
                "failures": case((window_over, 1), else_=_TABLE.c.failures + 1),
                "window_started_at": case((window_over, moment), else_=_TABLE.c.window_started_at),
                "lockouts": case((_TABLE.c.updated_at < moment - QUIET_PERIOD, 0), else_=_TABLE.c.lockouts),
                "updated_at": moment,
            },
        )
        .returning(_TABLE.c.failures, _TABLE.c.lockouts)
    )
    failures, lockouts = db.execute(counted).one()
    if failures >= rule.max_failures:
        length = min(rule.first_lock * (2**lockouts), rule.longest_lock)
        db.execute(
            update(LoginAttempt)
            .where(LoginAttempt.username_hash == key)
            .values(failures=0, lockouts=lockouts + 1, window_started_at=moment, locked_until=moment + length)
        )
    stale = (
        select(_TABLE.c.username_hash)
        .where(_TABLE.c.updated_at < moment - RETENTION, or_(_TABLE.c.locked_until.is_(None), _TABLE.c.locked_until < moment))
        .limit(CLEANUP_BATCH)
    )
    db.execute(delete(LoginAttempt).where(LoginAttempt.username_hash.in_(stale)))
    db.commit()


def clear(db: Session, rule: Rule, subject: str) -> None:
    """A right secret ends the count; does not commit, the sign-in that follows does."""
    db.execute(delete(LoginAttempt).where(LoginAttempt.username_hash == _key(rule, subject)))
