"""What the assignment service receives from the routes."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AssignmentDraft:
    date: date
    user_id: str
    note: str | None
    shift_code_id: str | None
    role_id: str | None


@dataclass(frozen=True)
class AssignmentChanges:
    """Only the fields that were sent, keyed by attribute name; a code or role sent empty is released."""

    values: dict
