"""What the board service hands to the mappers."""
from dataclasses import dataclass
from datetime import date

from app.models.day_off import DayOff
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


@dataclass(frozen=True)
class MonthBoard:
    month_start: date
    outlet_name: str | None
    assignments: list[Schedule]
    days_off: list[DayOff]
    shift_codes: list[ShiftCode]
