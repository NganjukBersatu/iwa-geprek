from pydantic import BaseModel, Field

from web.management.attendance_rules.constants import (
    MAX_AUTO_CLOSE_HOURS,
    MAX_PENALTY_PER_MINUTE,
    MAX_TOLERANCE_MINUTES,
    MIN_AUTO_CLOSE_HOURS,
)


class AttendanceRulesIn(BaseModel):
    """A field left out stays as it was."""

    late_tolerance_minutes: int | None = Field(None, ge=0, le=MAX_TOLERANCE_MINUTES, description="Minutes after the shift start that still count as on time")
    late_penalty_per_minute: int | None = Field(None, ge=0, le=MAX_PENALTY_PER_MINUTE, description="Rupiah per minute beyond the tolerance")
    auto_close_after_hours: int | None = Field(None, ge=MIN_AUTO_CLOSE_HOURS, le=MAX_AUTO_CLOSE_HOURS, description="Hours after the shift end when an open clock-in is closed by itself")


class AttendanceRulesOut(BaseModel):
    outlet_id: str
    late_tolerance_minutes: int
    late_penalty_per_minute: int
    auto_close_after_hours: int
    is_default: bool = Field(description="True when the branch has no settings row yet, so the defaults apply")
