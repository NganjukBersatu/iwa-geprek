"""Worked minutes of one attendance record, the single count used by the summary and the clock responses."""
from app.core.clock import as_aware, minutes_between
from app.employee.schedule.assignment import Window
from app.models.attendance import Attendance


def worked_minutes(record: Attendance, window: Window | None) -> int | None:
    """Owner rule: work counts only inside the shift, so an early arrival or a late clock-out adds nothing."""
    if window is None or record.clock_in_at is None or record.clock_out_at is None:
        return minutes_between(record.clock_in_at, record.clock_out_at)
    start = max(as_aware(record.clock_in_at), window[0])
    end = min(as_aware(record.clock_out_at), window[1])
    return minutes_between(start, end)
