from typing import Literal

from pydantic import BaseModel, Field

from web.management.shift_categories.constants import CLOCK_PATTERN, MAX_NAME_LENGTH


class ShiftCategoryUpdateIn(BaseModel):
    """A field left out stays; the kind or a clock sent as null is cleared, which switches the check off."""

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    shift_kind: Literal["work", "off"] | None = Field(None, description="work or off; empty means the category is not checked against day off")
    start_from: str | None = Field(None, pattern=CLOCK_PATTERN, description="Earliest start clock, HH:MM")
    start_until: str | None = Field(None, pattern=CLOCK_PATTERN, description="Latest start clock; earlier than start_from passes midnight")


class ShiftCategoryOut(BaseModel):
    id: str
    name: str
    shift_kind: Literal["work", "off"] | None
    start_from: str | None
    start_until: str | None
    codes: int = Field(description="Shift codes that use this category")
    mismatched: int = Field(description="Of those, the codes that do not fit the settings as they are now")
