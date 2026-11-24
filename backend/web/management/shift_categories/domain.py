"""What the shift category service receives from the routes and hands to the mappers."""
from dataclasses import dataclass

from app.models.category import Category


@dataclass(frozen=True)
class CategoryChanges:
    """[given] names the fields that were sent at all, so a value sent as None clears the setting."""

    given: frozenset[str]
    name: str | None = None
    shift_kind: str | None = None
    start_from: str | None = None
    start_until: str | None = None


@dataclass(frozen=True)
class CategoryEntry:
    category: Category
    codes: int
    mismatched: int
