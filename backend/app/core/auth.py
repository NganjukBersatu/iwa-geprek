"""Token authentication (header or browser cookie), sign-in sessions, permission checks, and branch resolution for v2 routes."""
from collections.abc import Callable
from dataclasses import dataclass
import logging
import secrets
from datetime import timedelta

from fastapi import Depends, HTTPException, Query, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.core import live, messages, money_trail
from app.core.clock import as_aware, now
from app.core.database import get_db
from app.core.brand import JWT_AUDIENCE, JWT_ISSUER, SESSION_COOKIE
from app.core.errors import CodedHTTPException
from app.core.security import hash_token
from app.core.settings import settings
from app.core.devices import device_layout
from app.models.device import REGISTERED, Device
from app.models.login_session import LoginSession
from app.models.outlet import Outlet
from app.models.user import User

log = logging.getLogger("cafe.auth")

# A missing header must reach current_user so it answers 401 like every other token failure.
bearer_scheme = HTTPBearer(auto_error=False)

MAX_OUTLETS_TO_INFER_SINGLE = 2
LAST_USED_STEP = timedelta(minutes=1)


SECONDS_PER_MINUTE = 60


JWT_TYPE = "at+jwt"
# 256 random bits; the token carries it, the database keeps only its hash, so a leaked table cannot be replayed.
SESSION_ID_BYTES = 32
CHANNEL_COOKIE = "cookie"
CHANNEL_BEARER = "bearer"
DEVICE_LABEL_LENGTH = 160
# Ended sessions are kept this long as a record of who signed in from where, then removed at that person's next sign-in.
ENDED_SESSION_DAYS = 30
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
OWN_SITE = frozenset({"same-origin", "none"})


def start_session(db: Session, user: User, channel: str, device_label: str | None) -> tuple[str, int]:
    """Commits a new sign-in and returns its token and lifetime in seconds; permissions stay out of the token, so a changed role applies at once."""
    started = now()
    lifetime = timedelta(minutes=settings.jwt_expire_minutes)
    db.execute(
        delete(LoginSession).where(
            LoginSession.user_id == user.id,
            LoginSession.expires_at < started - timedelta(days=ENDED_SESSION_DAYS),
        )
    )
    session_secret = secrets.token_urlsafe(SESSION_ID_BYTES)
    session = LoginSession(
        id=hash_token(session_secret),
        user_id=user.id,
        channel=channel,
        device_label=(device_label or "")[:DEVICE_LABEL_LENGTH] or None,
        created_at=started,
        last_seen_at=started,
        expires_at=started + lifetime,
    )
    db.add(session)
    db.commit()
    payload = {
        "sub": user.id,
        "sid": session_secret,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "username": user.username,
        "role_id": user.role_id,
        "exp": session.expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm, headers={"typ": JWT_TYPE})
    return token, settings.jwt_expire_minutes * SECONDS_PER_MINUTE


def end_session(db: Session, session_id: str) -> None:
    """Revokes one sign-in; the token of a revoked session is refused from then on."""
    session = db.get(LoginSession, session_id)
    if session is not None and session.revoked_at is None:
        session.revoked_at = now()
        db.commit()


def end_all_sessions(db: Session, user_id: str, keep: str | None = None) -> None:
    """Revokes every sign-in of one person except `keep`, the one making the change; the caller commits."""
    query = update(LoginSession).where(LoginSession.user_id == user_id, LoginSession.revoked_at.is_(None))
    if keep is not None:
        query = query.where(LoginSession.id != keep)
    db.execute(query.values(revoked_at=now()))


def end_sessions_of(db: Session, user_ids: list[str]) -> None:
    """Revokes every sign-in of many people in one statement; the caller commits."""
    if user_ids:
        db.execute(update(LoginSession).where(LoginSession.user_id.in_(user_ids), LoginSession.revoked_at.is_(None)).values(revoked_at=now()))


def session_cookie(response: Response, token: str, seconds: int) -> None:
    response.set_cookie(SESSION_COOKIE, token, max_age=seconds, path="/", secure=True, httponly=True, samesite="strict")


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="strict")


def _decode(token: str) -> dict:
    """Only a token this service signed, for this service, with the expected type; anything else is refused."""
    if jwt.get_unverified_header(token).get("typ") != JWT_TYPE:
        raise JWTError("unexpected token type")
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
        options={"require_exp": True, "require_iss": True, "require_aud": True},
    )


def session_subject(token: str) -> str | None:
    """The account a token names, or None when the token is not one this service signed; it does not look at the session row."""
    try:
        subject = _decode(token).get("sub")
    except JWTError:
        return None
    return subject if isinstance(subject, str) else None


def _mark_seen(db: Session, session: LoginSession) -> None:
    """Commits "last seen" at most once a minute, the precision the idle limit needs, without telling any screen."""
    seen = now()
    result = db.execute(
        update(LoginSession)
        .where(LoginSession.id == session.id, LoginSession.last_seen_at < seen - LAST_USED_STEP)
        .values(last_seen_at=seen)
        .execution_options(**live.SILENT)
    )
    if result.rowcount:
        db.commit()


def _idle_too_long(session: LoginSession) -> bool:
    """Only a browser is held to the idle limit; a tablet stays signed in for the whole shift."""
    limit = timedelta(minutes=settings.session_idle_minutes)
    return session.channel == CHANNEL_COOKIE and as_aware(session.last_seen_at) + limit <= now()


def _unauthorized() -> HTTPException:
    return CodedHTTPException(
        status.HTTP_401_UNAUTHORIZED,
        messages.INVALID_TOKEN,
        code="SESSION_INVALID",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _token_of(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str:
    """The header wins; a cookie-signed request that changes data must come from the site's own pages, which the browser states itself."""
    if credentials is not None:
        return credentials.credentials
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise _unauthorized()
    site = request.headers.get("sec-fetch-site")
    if request.method not in SAFE_METHODS and site is not None and site not in OWN_SITE:
        raise CodedHTTPException(status.HTTP_403_FORBIDDEN, messages.FOREIGN_SITE, code="FOREIGN_SITE")
    return token


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """The account and its sign-in are read again from the database, so a disabled account or a revoked session loses access at once."""
    try:
        payload = _decode(_token_of(request, credentials))
    except JWTError as error:
        raise _unauthorized() from error

    user_id = payload.get("sub")
    session_secret = payload.get("sid")
    if not user_id or not session_secret:
        raise _unauthorized()
    session = db.get(LoginSession, hash_token(session_secret))
    if session is None or session.user_id != user_id or session.revoked_at is not None or as_aware(session.expires_at) <= now():
        raise _unauthorized()
    if _idle_too_long(session):
        raise _unauthorized()
    # Every later use of the id (sign out, change of password) works with the stored hash, never with the secret.
    request.state.login_session_id = session.id
    _mark_seen(db, session)

    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise _unauthorized()
    if not user.is_active:
        raise CodedHTTPException(status.HTTP_403_FORBIDDEN, messages.ACCOUNT_DISABLED, code="ACCOUNT_DISABLED")
    money_trail.act_as(db, user.id)
    return user


def current_device(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Device:
    """A tablet signs in with the token it received when it was paired."""
    unknown = CodedHTTPException(status.HTTP_401_UNAUTHORIZED, messages.DEVICE_UNKNOWN, code="DEVICE_UNKNOWN", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unknown
    device = db.scalar(select(Device).where(Device.token_hash == hash_token(credentials.credentials), Device.status == REGISTERED))
    if device is None:
        raise unknown
    mark_used(db, device.id)
    # Dibaca DeviceLayoutMarker menjadi header X-Device-Layout, tanpa query tambahan.
    device_layout.mark(request, device.layout)
    return device


def mark_used(db: Session, device_id: str) -> None:
    """Commits "last used" at most once a minute, the precision it is shown in, without telling any screen."""
    seen = now()
    stale = or_(Device.last_used_at.is_(None), Device.last_used_at < seen - LAST_USED_STEP)
    result = db.execute(update(Device).where(Device.id == device_id, stale).values(last_used_at=seen).execution_options(**live.SILENT))
    if result.rowcount:
        db.commit()


@dataclass(frozen=True)
class FullAccessOnly:
    """The gate of a screen kept to full-access roles until the owner gives it a permission of its own."""


FULL_ACCESS_ONLY = FullAccessOnly()
# Full access, or a role ticked with this key, may use the management web at all.
PERMISSION_WEB = "web.masuk"


@dataclass(frozen=True)
class AnyOf:
    """Opens for whoever holds at least one of the keys."""

    keys: tuple[str, ...]


@dataclass(frozen=True)
class EveryUser:
    """Opens for every signed-in account, which may still see only its own rows."""


EVERY_USER = EveryUser()
# What opens a screen or a piece of one; every gate is checked by passes, so routes and the screen list never disagree.
Gate = str | AnyOf | FullAccessOnly | EveryUser


def passes(user: User, gate: Gate) -> bool:
    if isinstance(gate, EveryUser):
        return True
    if isinstance(gate, FullAccessOnly):
        return user.role is not None and user.role.has_full_access
    if isinstance(gate, AnyOf):
        return any(user.allows(key) for key in gate.keys)
    return user.allows(gate)


def may_enter_web(user: User) -> bool:
    return user.allows(PERMISSION_WEB)


def _denied(user: User, gate: Gate) -> HTTPException:
    if isinstance(gate, FullAccessOnly):
        return CodedHTTPException(status.HTTP_403_FORBIDDEN, messages.FULL_ACCESS_DENIED, code="FULL_ACCESS_REQUIRED")
    keys = gate.keys if isinstance(gate, AnyOf) else (str(gate),)
    role_name = user.role.name if user.role else messages.NO_ROLE
    # The role and permission stay in the log; the person is only told they have no access.
    log.warning("access denied: user=%s role=%s needs=%s", user.id, role_name, ", ".join(keys))
    return CodedHTTPException(status.HTTP_403_FORBIDDEN, messages.PERMISSION_DENIED, code="PERMISSION_DENIED")


def require_gate(gate: Gate) -> Callable[..., User]:
    def guard(user: User = Depends(current_user)) -> User:
        if not passes(user, gate):
            raise _denied(user, gate)
        return user

    return guard


require_full_access = require_gate(FULL_ACCESS_ONLY)


def require_permission(permission: str) -> Callable[..., User]:
    return require_gate(permission)


def readable_outlet_id(
    outlet_id: str | None = Query(None, description="Only for accounts without a branch; empty means every branch"),
    user: User = Depends(current_user),
) -> str | None:
    """Branch-bound accounts only ever read their own branch, whatever the URL says."""
    return user.locked_outlet_id or outlet_id


def writable_outlet_id(
    outlet_id: str | None = Query(None, description="Only for accounts without a branch; ignored otherwise"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> str:
    """Branch-bound accounts always write to their own branch, whatever the URL says."""
    locked = user.locked_outlet_id
    if locked:
        return locked
    if outlet_id:
        return outlet_id

    outlets = db.scalars(select(Outlet.id).limit(MAX_OUTLETS_TO_INFER_SINGLE)).all()
    if len(outlets) == 1:
        return outlets[0]
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.BRANCH_REQUIRED)
