"""What the shift code group service receives from the routes and hands to the mappers."""
from dataclasses import dataclass, field

from app.models.outlet import Outlet
from app.models.shift_code import ShiftCode


@dataclass(frozen=True)
class GroupDraft:
    category: str
    code: str
    start_clock: str | None
    end_clock: str | None
    overtime_start_clock: str | None
    overtime_end_clock: str | None
    color: str | None
    is_day_off: bool
    sort_order: int
    outlet_ids: tuple[str, ...]
    crosses_midnight: bool = False


@dataclass(frozen=True)
class GroupChanges:
    """Only the fields that were sent, keyed by attribute name; [outlet_ids] None leaves the branches as they are."""

    values: dict
    category: str | None = None
    outlet_ids: tuple[str, ...] | None = None
    crosses_midnight: bool | None = None


@dataclass(frozen=True)
class CodeGroup:
    """One shift code as a person thinks of it, kept as one row per branch underneath."""

    key: str
    rows: list[ShiftCode]
    branches: list[Outlet]
    assignments: int
    category: str = ""

    @property
    def first(self) -> ShiftCode:
        return self.rows[0]


@dataclass(frozen=True)
class GroupList:
    groups: list[CodeGroup] = field(default_factory=list)
