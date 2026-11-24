"""What the role service receives from the routes."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDraft:
    name: str
    description: str | None
    permissions: list[str]
    sort_order: int
    is_protected: bool
    station_id: str | None


@dataclass(frozen=True)
class RoleChanges:
    """None means unchanged, except the description and the station, which their `_given` flags tell apart from clearing them."""

    name: str | None
    description: str | None
    description_given: bool
    permissions: list[str] | None
    sort_order: int | None
    is_protected: bool | None
    station_id: str | None
    station_given: bool
