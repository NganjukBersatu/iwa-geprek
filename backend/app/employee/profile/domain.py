"""What the profile service hands to the mappers."""
from dataclasses import dataclass

from app.models.user import User


@dataclass(frozen=True)
class Profile:
    user: User
    outlet_name: str | None
