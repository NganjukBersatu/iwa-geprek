from pydantic import BaseModel, Field

from typing import Literal

from web.management.shift_codes.constants import CLOCK_PATTERN, COLOR_PATTERN, DEFAULT_SORT_ORDER, MAX_CODE_LENGTH


class ShiftCodeCreateIn(BaseModel):
    category_id: str = Field(min_length=1)
    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)
    start_clock: str | None = Field(None, pattern=CLOCK_PATTERN, description="HH:MM; an end before the start passes midnight")
    end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_start_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    color: str | None = Field(None, pattern=COLOR_PATTERN)
    is_day_off: bool = False
    sort_order: int = DEFAULT_SORT_ORDER
    crosses_midnight: bool = Field(False, description="The admin's statement that the end clock falls on the next day; required when the end is earlier than the start")


class ShiftCodeUpdateIn(BaseModel):
    """A field left out stays; a clock or color sent empty is cleared, while an empty category, code, day-off flag or order is ignored."""

    category_id: str | None = None
    code: str | None = Field(None, min_length=1, max_length=MAX_CODE_LENGTH)
    start_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_start_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    color: str | None = Field(None, pattern=COLOR_PATTERN)
    is_day_off: bool | None = None
    sort_order: int | None = None
    crosses_midnight: bool | None = Field(None, description="Required as true when the new clocks put the end earlier than the start")


class ShiftCodeOut(BaseModel):
    id: str
    outlet_id: str
    category: str = Field(description="Category name, for display")
    category_id: str | None
    code: str
    start_clock: str | None
    end_clock: str | None
    overtime_start_clock: str | None
    overtime_end_clock: str | None
    color: str | None
    is_day_off: bool
    sort_order: int
    crosses_midnight: bool = Field(description="The end clock falls on the next day")
    clock_problem: Literal["same_clock", "too_long"] | None = Field(description="A saved code whose hours are not reasonable and need a look")
