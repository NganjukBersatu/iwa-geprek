"""Turns assignments into response schemas."""
from app.models.schedule import Schedule
from web.management.schedule.assignments.schemas import AssignmentOut


def assignment_out(schedule: Schedule) -> AssignmentOut:
    return AssignmentOut(
        id=schedule.id,
        date=schedule.date,
        user_id=schedule.user_id,
        user_username=schedule.user.username,
        note=schedule.note,
        shift_code_id=schedule.shift_code_id,
        role_id=schedule.role_id,
        role_name=schedule.role.name if schedule.role else None,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )
