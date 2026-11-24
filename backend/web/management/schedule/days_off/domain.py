"""What the day-off service receives from the routes."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DayOffDraft:
    date: date
    user_id: str
    shift_code_id: str | None
    note: str | None
