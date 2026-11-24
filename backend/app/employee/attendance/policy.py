"""The attendance rules a branch has chosen: lateness tolerance, penalty rate, and auto-close delay."""
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.employee.attendance.constants import (
    DEFAULT_AUTO_CLOSE_HOURS,
    DEFAULT_LATE_PENALTY_PER_MINUTE,
    DEFAULT_LATE_TOLERANCE_MINUTES,
)
from app.models.attendance import AttendanceStatus
from app.models.cafe_settings import CafeSettings


@dataclass(frozen=True)
class BranchPolicy:
    late_tolerance_minutes: int = DEFAULT_LATE_TOLERANCE_MINUTES
    late_penalty_per_minute: int = DEFAULT_LATE_PENALTY_PER_MINUTE
    auto_close_after_hours: int = DEFAULT_AUTO_CLOSE_HOURS

    @classmethod
    def load(cls, db: Session, outlet_id: str) -> "BranchPolicy":
        """A branch without a settings row follows the defaults."""
        settings = db.get(CafeSettings, outlet_id)
        if settings is None:
            return cls()
        return cls(
            late_tolerance_minutes=settings.late_tolerance_minutes,
            late_penalty_per_minute=settings.late_penalty_per_minute,
            auto_close_after_hours=settings.auto_close_after_hours,
        )

    @classmethod
    def load_many(cls, db: Session, outlet_ids: set[str]) -> dict[str, "BranchPolicy"]:
        """The rules of several branches in one query; a branch without a settings row follows the defaults."""
        found = {settings.outlet_id: settings for settings in db.scalars(select(CafeSettings).where(CafeSettings.outlet_id.in_(outlet_ids))).all()} if outlet_ids else {}
        return {
            outlet_id: cls()
            if outlet_id not in found
            else cls(
                late_tolerance_minutes=found[outlet_id].late_tolerance_minutes,
                late_penalty_per_minute=found[outlet_id].late_penalty_per_minute,
                auto_close_after_hours=found[outlet_id].auto_close_after_hours,
            )
            for outlet_id in outlet_ids
        }

    @property
    def auto_close_grace(self) -> timedelta:
        return timedelta(hours=self.auto_close_after_hours)

    def status_for(self, late_minutes: int) -> AttendanceStatus:
        return AttendanceStatus.LATE if late_minutes > self.late_tolerance_minutes else AttendanceStatus.PRESENT

    def penalty(self, late_minutes: int) -> int:
        """Only the minutes beyond the tolerance are charged, at a flat rate per minute."""
        return max(0, late_minutes - self.late_tolerance_minutes) * self.late_penalty_per_minute
