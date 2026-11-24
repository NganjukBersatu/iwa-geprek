"""Turns days off into response schemas."""
from app.models.day_off import DayOff
from web.management.schedule.days_off.schemas import DayOffOut


def day_off_out(day_off: DayOff) -> DayOffOut:
    return DayOffOut(
        id=day_off.id,
        date=day_off.date,
        user_id=day_off.user_id,
        user_username=day_off.user.username,
        shift_code_id=day_off.shift_code_id,
        note=day_off.note,
    )
