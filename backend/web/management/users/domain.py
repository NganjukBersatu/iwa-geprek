"""What the user service receives from the routes and hands to the mappers."""
from dataclasses import dataclass
from app.models.user import User


@dataclass(frozen=True)
class UserDraft:
    name: str
    username: str
    password: str
    role_id: str
    outlet_id: str | None
    personal: dict


@dataclass(frozen=True)
class UserChanges:
    """None means unchanged; `personal` holds only the personal fields that were sent, so an empty one clears it."""

    name: str | None
    username: str | None
    password: str | None
    role_id: str | None
    outlet_id: str | None
    is_active: bool | None
    personal: dict


@dataclass(frozen=True)
class UserPage:
    items: list[User]
    total: int
    page: int
    size: int
