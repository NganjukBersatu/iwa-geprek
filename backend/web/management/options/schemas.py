from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.catalog.recipe_schemas import CopiedIngredientOut

MAX_GROUP_NAME = 80
MAX_CHOICE_NAME = 60
MAX_EXTRA_NAME = 80


class OptionRecipeLineOut(BaseModel):
    ingredient_id: str
    ingredient_name: str
    unit: str | None
    qty: Decimal


class ChoiceIn(BaseModel):
    # Sent for an existing choice so its id and recipe stay; empty makes a new one.
    id: str | None = None
    name: str = Field(min_length=1, max_length=MAX_CHOICE_NAME)
    color: str | None = None
    is_active: bool = True


class VariantChoiceOut(BaseModel):
    id: str
    name: str
    color: str | None
    is_active: bool
    recipe: list[OptionRecipeLineOut]


class VariantGroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_GROUP_NAME)
    required: bool = True
    is_active: bool = True
    choices: list[ChoiceIn] = Field(min_length=1)
    menu_ids: list[str] = []
    # Kosong berlaku di semua cabang; terisi milik satu cabang itu saja.
    outlet_id: str | None = None


class VariantGroupUpdateIn(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=MAX_GROUP_NAME)
    required: bool | None = None
    is_active: bool | None = None
    choices: list[ChoiceIn] | None = Field(None, min_length=1)
    menu_ids: list[str] | None = None
    # Dikirim kosong berarti berlaku di semua cabang; tidak dikirim tidak berubah.
    outlet_id: str | None = None


class ManagedVariantGroupOut(BaseModel):
    id: str
    name: str
    required: bool
    is_active: bool
    choices: list[VariantChoiceOut]
    menu_ids: list[str]
    outlet_id: str | None


class ExtraIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_EXTRA_NAME)
    price: Decimal = Field(ge=0)
    is_active: bool = True
    # Empty sells the extra everywhere; a list limits it to those branches.
    outlet_ids: list[str] | None = None
    branch_prices: dict[str, Decimal | None] | None = None
    category_id: str | None = None
    menu_ids: list[str] = []


class ExtraUpdateIn(BaseModel):
    """A field left out stays; outlet_ids sent empty sells the extra everywhere again."""

    name: str | None = Field(None, min_length=1, max_length=MAX_EXTRA_NAME)
    price: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    outlet_ids: list[str] | None = None
    branch_prices: dict[str, Decimal | None] | None = None
    category_id: str | None = None
    menu_ids: list[str] | None = None


class ManagedExtraOut(BaseModel):
    id: str
    name: str
    price: Decimal
    is_active: bool
    outlet_ids: list[str] | None
    branch_prices: dict[str, Decimal]
    category_id: str | None
    category_name: str | None
    menu_ids: list[str]
    recipe: list[OptionRecipeLineOut]


class OptionRecipeLineIn(BaseModel):
    ingredient_id: str
    qty: Decimal = Field(gt=0)


class OptionRecipeIn(BaseModel):
    """The ingredients one choice or extra uses on top of the menu's own recipe; empty uses up nothing."""

    lines: list[OptionRecipeLineIn]
    all_branches: bool = False


class OptionRecipeOut(BaseModel):
    recipe: list[OptionRecipeLineOut]
    branches: int
    copied: list[CopiedIngredientOut]


class ExtraCategoryOut(BaseModel):
    id: str
    name: str


class OptionMenuOut(BaseModel):
    id: str
    name: str
