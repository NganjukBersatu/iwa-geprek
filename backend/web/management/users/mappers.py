"""Turns user accounts into response schemas."""

from app.core import protection
from app.core.http import static_url
from app.models.user import User
from web.management.roles.service import effective_permissions
from web.management.users.domain import UserPage
from web.management.users.schemas import UserOut, UserPageOut


def user_out(user: User, base_url: str, viewer: User) -> UserOut:
    role = user.role
    return UserOut(
        id=user.id,
        name=user.name,
        username=user.username,
        role_id=user.role_id,
        role_name=role.name if role else "-",
        permissions=effective_permissions(role) if role else [],
        outlet_id=user.outlet_id,
        is_active=user.is_active,
        created_at=user.created_at,
        photo_url=static_url(base_url, user.photo_key),
        phone=user.phone,
        address=user.address,
        birth_date=user.birth_date,
        gender=user.gender,
        email=user.email,
        emergency_name=user.emergency_name,
        emergency_phone=user.emergency_phone,
        emergency_relation=user.emergency_relation,
        joined_date=user.joined_date,
        locked=not protection.can_manage_account(viewer, user),
    )


def page_out(page: UserPage, base_url: str, viewer: User) -> UserPageOut:
    return UserPageOut(
        items=[user_out(user, base_url, viewer) for user in page.items], total=page.total, page=page.page, size=page.size
    )
