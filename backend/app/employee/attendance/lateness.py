"""Lateness arithmetic."""
from datetime import datetime

from app.core.clock import SECONDS_PER_MINUTE, as_aware


def minutes_late(clock_in_at: datetime, starts_at: datetime) -> int:
    """Whole minutes after the start, rounded down; zero for an early arrival."""
    seconds = int((as_aware(clock_in_at) - as_aware(starts_at)).total_seconds())
    return max(0, seconds // SECONDS_PER_MINUTE)
