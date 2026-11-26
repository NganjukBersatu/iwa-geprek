from pydantic import BaseModel, Field

from web.management.roles.constants import DEFAULT_SORT_ORDER, MAX_DESCRIPTION_LENGTH, MAX_NAME_LENGTH


class RoleCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    permissions: list[str] = Field(default_factory=list, description="Catalog keys; unknown keys are dropped, not rejected")
    sort_order: int = DEFAULT_SORT_ORDER
    is_protected: bool = False
    station_id: str | None = Field(default=None, description="The station the tablet shows to accounts in this role; null for none")


class RoleUpdateIn(BaseModel):
    """A field left out stays as it was; an empty description clears it."""

    name: str | None = Field(default=None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    permissions: list[str] | None = None
    sort_order: int | None = None
    is_protected: bool | None = None
    station_id: str | None = Field(default=None, description="Sent as null to clear it; left out stays as it was")


class RoleOut(BaseModel):
    id: str
    name: str
    description: str | None
    permissions: list[str] = Field(description="Effective permissions; a full-access role lists the whole catalog")
    is_default: bool
    full_access: bool = Field(description="Owner or Admin: every permission, and the boxes cannot be unticked")
    sort_order: int
    is_protected: bool
    station_id: str | None
    locked: bool = Field(description="True when the viewer may not change this role; a protected role can be changed by its holders and its creator, and deleted by no one")
    held_by_viewer: bool = Field(description="The signed-in account holds this role, which is what lets it mark other roles as protected")
    assignable: bool = Field(description="True when the viewer may put an account in this role")


class RoleStationOut(BaseModel):
    """Pilihan stasiun untuk peran."""

    id: str
    name: str


class PermissionOut(BaseModel):
    key: str
    label: str
    group: str
    group_name: str
    section: str
    description: str
    default_for_new_role: bool
    in_cashier_example: bool
