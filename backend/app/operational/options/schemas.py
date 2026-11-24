from decimal import Decimal

from pydantic import BaseModel, Field

MAX_GROUP_NAME = 80
MAX_CHOICE_NAME = 60
MAX_EXTRA_NAME = 80


class ChoiceIn(BaseModel):
    # Sent for an existing choice so its id, color and recipe stay; empty makes a new one.
    id: str | None = None
    name: str = Field(min_length=1, max_length=MAX_CHOICE_NAME)
    color: str | None = None
    is_active: bool = True


class OptionChoiceOut(BaseModel):
    id: str
    name: str
    color: str | None
    is_active: bool


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_GROUP_NAME)
    required: bool = True
    is_active: bool = True
    choices: list[ChoiceIn] = Field(min_length=1)
    menu_ids: list[str] = []


class OptionGroupOut(BaseModel):
    id: str
    name: str
    required: bool
    is_active: bool
    choices: list[OptionChoiceOut]
    menu_ids: list[str]
    # Benar bila kelompok ini milik cabang tablet saja; yang berlaku di semua cabang diubah dari web admin.
    editable: bool


class OptionExtraIn(BaseModel):
    """Branch limits, branch prices and the category stay as the web set them; the tablet does not touch them."""

    name: str = Field(min_length=1, max_length=MAX_EXTRA_NAME)
    price: Decimal = Field(ge=0)
    is_active: bool = True
    menu_ids: list[str] = []


class OptionExtraOut(BaseModel):
    id: str
    name: str
    price: Decimal
    is_active: bool
    menu_ids: list[str]
    # Benar bila ekstra ini hanya untuk cabang tablet; yang lebih luas diubah dari web admin.
    editable: bool


class MenuChoiceOut(BaseModel):
    id: str
    name: str
