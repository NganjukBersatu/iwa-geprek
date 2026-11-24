"""Turns schedule rows into response schemas."""
from app.core.period import month_label
from app.employee.schedule.board.domain import MonthBoard
from app.employee.schedule.board.schemas import BoardAssignmentOut, BoardDayOffOut, MonthBoardOut, BoardShiftCodeOut
from app.models.day_off import DayOff
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode


def assignment_out(schedule: Schedule) -> BoardAssignmentOut:
    return BoardAssignmentOut(
        id=schedule.id,
        date=schedule.date,
        user_id=schedule.user_id,
        user_username=schedule.user.username,
        user_name=schedule.user.name,
        shift_code_id=schedule.shift_code_id,
        role_name=schedule.role.name if schedule.role else None,
        note=schedule.note,
        starts_at=schedule.starts_at,
        ends_at=schedule.ends_at,
    )


def day_off_out(day_off: DayOff) -> BoardDayOffOut:
    return BoardDayOffOut(
        id=day_off.id,
        date=day_off.date,
        user_id=day_off.user_id,
        user_username=day_off.user.username,
        user_name=day_off.user.name,
        shift_code_id=day_off.shift_code_id,
        note=day_off.note,
    )


def shift_code_out(code: ShiftCode) -> BoardShiftCodeOut:
    return BoardShiftCodeOut(
        id=code.id,
        code=code.code,
        category=code.category.name if code.category else None,
        start_clock=code.start_clock,
        end_clock=code.end_clock,
        overtime_start_clock=code.overtime_start_clock,
        overtime_end_clock=code.overtime_end_clock,
        color=code.color,
        is_day_off=code.is_day_off,
        duration_minutes=code.duration_minutes,
    )


def month_board_out(board: MonthBoard) -> MonthBoardOut:
    return MonthBoardOut(
        month=month_label(board.month_start),
        outlet_name=board.outlet_name,
        assignments=[assignment_out(item) for item in board.assignments],
        days_off=[day_off_out(item) for item in board.days_off],
        shift_codes=[shift_code_out(item) for item in board.shift_codes],
    )
