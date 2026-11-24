"""Turns roles and the catalog into response schemas."""
from app.core import protection
from app.core.sorting import RowSorting
from app.models.role import Role
from app.models.user import User
from app.core.permissions.registry import GROUPS
from web.management.roles.schemas import PermissionOut, RoleOut
from web.management.roles.service import effective_permissions


SORTING: RowSorting[RoleOut] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "description": lambda row: row.description,
        "permissions": lambda row: len(row.permissions),
    },
    identity=lambda row: row.id,
)


def role_out(role: Role, viewer: User) -> RoleOut:
    return RoleOut(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=effective_permissions(role),
        is_default=bool(role.is_default),
        full_access=role.has_full_access,
        sort_order=role.sort_order,
        is_protected=bool(role.is_protected),
        station_id=role.station_id,
        locked=not protection.can_use_role(viewer, role),
        held_by_viewer=protection.holds(viewer, role),
        assignable=protection.can_give_role(viewer, role),
    )


def catalog_out() -> list[PermissionOut]:
    return [
        PermissionOut(
            key=permission.key,
            label=permission.label,
            group=group.key,
            group_name=group.name,
            section=section.name,
            description=permission.description,
            default_for_new_role=permission.default_for_new_role,
        )
        for group in GROUPS
        for section in group.sections
        for permission in section.permissions
    ]
