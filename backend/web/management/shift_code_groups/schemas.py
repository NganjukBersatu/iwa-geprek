from typing import Literal

from pydantic import BaseModel, Field

from web.management.shift_code_groups.constants import CLOCK_PATTERN, COLOR_PATTERN, MAX_CATEGORY_LENGTH, MAX_CODE_LENGTH


class CodeGroupCreateIn(BaseModel):
    category: str = Field(min_length=1, max_length=MAX_CATEGORY_LENGTH, description="Found by name, or made when new")
    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)
    start_clock: str | None = Field(None, pattern=CLOCK_PATTERN, description="HH:MM; an end before the start passes midnight")
    end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_start_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    color: str | None = Field(None, pattern=COLOR_PATTERN)
    is_day_off: bool = False
    sort_order: int = 0
    crosses_midnight: bool = Field(False, description="The admin's statement that the end clock falls on the next day; required when the end is earlier than the start")
    outlet_ids: list[str] = Field(description="Branches that use this code; an account bound to one branch gets that branch whatever it sends")


class CodeGroupUpdateIn(BaseModel):
    """A field left out stays; a clock or color sent empty is cleared. Branches sent replace the current ones."""

    category: str | None = Field(None, max_length=MAX_CATEGORY_LENGTH)
    code: str | None = Field(None, min_length=1, max_length=MAX_CODE_LENGTH)
    start_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_start_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    overtime_end_clock: str | None = Field(None, pattern=CLOCK_PATTERN)
    color: str | None = Field(None, pattern=COLOR_PATTERN)
    is_day_off: bool | None = None
    sort_order: int | None = None
    crosses_midnight: bool | None = Field(None, description="Required as true when the new clocks put the end earlier than the start")
    outlet_ids: list[str] | None = None


class ShiftCodeGroupBranchOut(BaseModel):
    id: str
    name: str


class CodeGroupOut(BaseModel):
    id: str = Field(description="Names the code across its branches")
    code: str
    category: str
    start_clock: str | None
    end_clock: str | None
    overtime_start_clock: str | None
    overtime_end_clock: str | None
    color: str | None
    is_day_off: bool
    sort_order: int
    crosses_midnight: bool = Field(description="The end clock falls on the next day")
    clock_problem: Literal["same_clock", "too_long"] | None = Field(description="A saved code whose hours are not reasonable and need a look")
    branches: list[ShiftCodeGroupBranchOut]
    assignments: int = Field(description="Schedule entries that use the code now, which lose it if the code is deleted")
