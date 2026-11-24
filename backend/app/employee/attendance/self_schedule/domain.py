"""What the self-made schedule service hands to the mappers."""
from dataclasses import dataclass
from datetime import date, datetime

from app.models.outlet import Outlet
from app.models.role import Role
from app.models.shift_code import ShiftCode


@dataclass(frozen=True)
class Suggestion:
    """A shift code of the branch on the day whose start falls within the allowed range of now."""

    code: ShiftCode
    day: date
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class Options:
    outlets: list[Outlet]
    roles: list[Role]
    suggestions: list[Suggestion]
