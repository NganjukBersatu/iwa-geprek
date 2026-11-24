"""Why the clock-in button is not offered, so the screen can say so instead of staying silent."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.clock import as_aware
from app.employee.attendance.constants import BLOCK_ALREADY_USED, BLOCK_ENDED, BLOCK_NO_SCHEDULE, BLOCK_NOT_OPEN_YET
from app.employee.schedule.constants import CLOCK_IN_EARLY_MINUTES
from app.models.schedule import Schedule

EARLY = timedelta(minutes=CLOCK_IN_EARLY_MINUTES)


@dataclass(frozen=True)
class ClockInBlock:
    """`at` is when the clock-in opens for a coming assignment, or when an ended one finished."""

    reason: str
    schedule: Schedule | None
    at: datetime | None


def find(schedules: list[Schedule], at: datetime) -> ClockInBlock:
    """A coming assignment is named first, then one already clocked in, then one that ended without a clock-in."""
    coming = [item for item in schedules if as_aware(item.starts_at) - EARLY > at]
    if coming:
        first = min(coming, key=lambda item: as_aware(item.starts_at))
        return ClockInBlock(BLOCK_NOT_OPEN_YET, first, as_aware(first.starts_at) - EARLY)

    running = [item for item in schedules if item.clock_in_used and as_aware(item.ends_at) >= at]
    if running:
        return ClockInBlock(BLOCK_ALREADY_USED, min(running, key=lambda item: as_aware(item.starts_at)), None)

    missed = [item for item in schedules if not item.clock_in_used and as_aware(item.ends_at) < at]
    if missed:
        last = max(missed, key=lambda item: as_aware(item.ends_at))
        return ClockInBlock(BLOCK_ENDED, last, as_aware(last.ends_at))

    return ClockInBlock(BLOCK_NO_SCHEDULE, None, None)
