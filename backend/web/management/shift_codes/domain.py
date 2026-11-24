"""What the shift code service receives from the routes."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ShiftCodeDraft:
    category_id: str
    code: str
    start_clock: str | None
    end_clock: str | None
    overtime_start_clock: str | None
    overtime_end_clock: str | None
    color: str | None
    is_day_off: bool
    sort_order: int
    crosses_midnight: bool = False


@dataclass(frozen=True)
class ShiftCodeChanges:
    """Only the fields that were sent, keyed by attribute name; [crosses_midnight] is the admin's statement about the clocks and is not stored."""

    values: dict
    crosses_midnight: bool | None = None
