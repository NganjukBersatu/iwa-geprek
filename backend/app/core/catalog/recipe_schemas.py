from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

MAX_ADD_COST_PERCENT = 500
MAX_RUPIAH = 100_000_000
MAX_TARGET = 100


class RecipeLineIn(BaseModel):
    ingredient_id: str
    # The amount for one portion, in the ingredient's own unit.
    qty: Decimal = Field(gt=0)


class RecipeSaveIn(BaseModel):
    """The whole recipe at once; an empty list removes it. Each costing setting not sent stays, sent empty follows the default."""

    lines: list[RecipeLineIn]
    add_cost_kind: Literal["persen", "rupiah"] | None = None
    add_cost_value: Decimal | None = Field(None, ge=0)
    overhead: Decimal | None = Field(None, ge=0, le=MAX_RUPIAH)
    target_margin_percent: Decimal | None = Field(None, gt=0, lt=MAX_TARGET)
    # True: resep yang sama disimpan di setiap cabang aktif lain; bahan yang belum ada disalin dengan stok 0.
    all_branches: bool = False

    @model_validator(mode="after")
    def _limits(self):
        if self.add_cost_kind and self.add_cost_value is None:
            raise ValueError("Isi nilai add cost.")
        if self.add_cost_kind == "persen" and (self.add_cost_value or 0) > MAX_ADD_COST_PERCENT:
            raise ValueError("Add cost persen maksimal 500.")
        if self.add_cost_kind == "rupiah" and (self.add_cost_value or 0) > MAX_RUPIAH:
            raise ValueError("Add cost rupiah terlalu besar.")
        return self


class RecipeLineOut(BaseModel):
    ingredient_id: str
    ingredient_name: str
    unit: str | None
    qty: Decimal
    # Empty for a reader who may see the recipe but not its cost.
    unit_price: Decimal | None
    cost: Decimal | None


class RecipeOut(BaseModel):
    outlet_id: str
    outlet_name: str
    menu_id: str
    menu_name: str
    category_name: str | None
    price: Decimal
    has_recipe: bool
    lines: list[RecipeLineOut]
    # Every figure below is empty for a reader without recipe cost access.
    ingredients_cost: Decimal | None
    add_cost_kind: str | None
    add_cost_value: Decimal | None
    add_cost_custom: bool
    add_cost: Decimal | None
    overhead: Decimal | None
    final_cost: Decimal | None
    margin: Decimal | None
    margin_percent: Decimal | None
    target_margin_percent: Decimal | None
    target_custom: bool
    suggested_price: Decimal | None


class RecipePageOut(BaseModel):
    items: list[RecipeOut]
    total: int
    page: int
    size: int


class CopiedIngredientOut(BaseModel):
    branch_name: str
    ingredient_name: str


class RecipeSaveOut(BaseModel):
    recipe: RecipeOut
    branches: int
    copied: list[CopiedIngredientOut]


class IngredientOptionOut(BaseModel):
    id: str
    name: str
    unit: str | None
    unit_price: Decimal | None
