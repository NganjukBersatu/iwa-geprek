"""Turns the signed-in user member into its response schema."""
from app.auth.schemas import AuthUserOut, BrowserSessionOut, TokenOut
from app.core.auth import may_enter_web
from app.core.http import static_url
from app.models.user import User

NO_ROLE = "-"


def user_out(user: User, base_url: str) -> AuthUserOut:
    role = user.role
    return AuthUserOut(
        id=user.id,
        name=user.name,
        username=user.username,
        role_id=user.role_id,
        role_name=role.name if role else NO_ROLE,
        permissions=[] if role is None or role.has_full_access else sorted(role.permissions or []),
        full_access=role is not None and role.has_full_access,
        web_access=may_enter_web(user),
        outlet_id=user.outlet_id,
        station_id=role.station_id if role else None,
        is_active=user.is_active,
        photo_url=static_url(base_url, user.photo_key),
    )


def token_out(user: User, token: str, lifetime_seconds: int, base_url: str) -> TokenOut:
    return TokenOut(access_token=token, expires_in=lifetime_seconds, user=user_out(user, base_url))


def session_out(user: User, lifetime_seconds: int, base_url: str) -> BrowserSessionOut:
    return BrowserSessionOut(expires_in=lifetime_seconds, user=user_out(user, base_url))
