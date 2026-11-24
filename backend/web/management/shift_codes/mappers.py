"""Turns shift codes into response schemas."""
from app.models.shift_code import ShiftCode
from web.management.shift_codes import clock_rules
from web.management.shift_codes.schemas import ShiftCodeOut


def shift_code_out(shift_code: ShiftCode) -> ShiftCodeOut:
    return ShiftCodeOut(
        id=shift_code.id,
        outlet_id=shift_code.outlet_id,
        category=shift_code.category.name if shift_code.category else "",
        category_id=shift_code.category_id,
        code=shift_code.code,
        start_clock=shift_code.start_clock,
        end_clock=shift_code.end_clock,
        overtime_start_clock=shift_code.overtime_start_clock,
        overtime_end_clock=shift_code.overtime_end_clock,
        color=shift_code.color,
        is_day_off=shift_code.is_day_off,
        sort_order=shift_code.sort_order,
        crosses_midnight=_crosses_midnight(shift_code.start_clock, shift_code.end_clock),
        clock_problem=clock_rules.problem(shift_code.start_clock, shift_code.end_clock),
    )


def _crosses_midnight(start_clock: str | None, end_clock: str | None) -> bool:
    return bool(start_clock and end_clock and end_clock < start_clock)
