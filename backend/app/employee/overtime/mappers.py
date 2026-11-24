"""Turns overtime entries into response schemas."""
from app.core.clock import minutes_between
from app.employee.overtime.ledger import Entry
from app.employee.overtime.schemas import OvertimeOut


def overtime_out(entry: Entry) -> OvertimeOut:
    return OvertimeOut(
        id=entry.id,
        date=entry.date,
        started_at=entry.start_at,
        ended_at=entry.end_at,
        minutes=minutes_between(entry.start_at, entry.end_at) or 0,
        scheduled=entry.scheduled,
        note=entry.note,
    )
