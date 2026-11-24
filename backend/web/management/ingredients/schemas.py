from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.ingredients.stock_level import StockLevel
from web.management.ingredients import constants as c


class IngredientCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=c.MAX_NAME_LENGTH)
    unit_id: str = Field(min_length=1)
    category_id: str | None = None
    package_price: Decimal = Field(Decimal(0), ge=0, description="Price of one package")
    package_size: Decimal = Field(Decimal(1), gt=0, description="How many units one package holds")
    unit_price: Decimal | None = Field(None, ge=0, description="Left out, it starts as package price over package size; after that it is manual")
    shrink_tolerance: Decimal = Field(Decimal(0), ge=0, le=c.MAX_SHRINK_PERCENT)
    minimum: Decimal = Field(Decimal(0), ge=0)
    is_indirect: bool = Field(False, description="Not taken from stock by a recipe; users write its use by hand")


class IngredientUpdateIn(BaseModel):
    """A field left out stays as it was; a unit sent null is not changed."""

    name: str | None = Field(None, min_length=1, max_length=c.MAX_NAME_LENGTH)
    unit_id: str | None = None
    category_id: str | None = None
    package_price: Decimal | None = Field(None, ge=0)
    package_size: Decimal | None = Field(None, gt=0)
    unit_price: Decimal | None = Field(None, ge=0)
    shrink_tolerance: Decimal | None = Field(None, ge=0, le=c.MAX_SHRINK_PERCENT)
    minimum: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    is_available: bool | None = None
    is_indirect: bool | None = Field(None, description="Refused while a recipe still uses the ingredient")


class IngredientOut(BaseModel):
    id: str
    outlet_id: str
    catalog_id: str | None = Field(description="None while the ingredient is not yet linked to the shared catalog")
    branch_count: int = Field(description="How many branches share the catalog entry, this one included; renaming reaches all of them")
    name: str
    category_id: str | None
    category: str | None
    unit_id: str | None
    unit: str
    photo_url: str | None
    package_price: Decimal
    package_size: Decimal
    unit_price: Decimal
    shrink_tolerance: Decimal
    minimum: Decimal
    is_active: bool
    is_available: bool
    is_indirect: bool
    balance: Decimal
    stock_level: StockLevel | None = Field(description="negative below zero, out at zero, low at the minimum; None while stock is enough")
    is_low: bool = Field(description="The balance has reached the minimum")
    days_since_move: int | None
    is_dormant: bool = Field(description="Stock is held but has not moved for a long time")
    created_at: datetime
    updated_at: datetime


class IngredientPageOut(BaseModel):
    items: list[IngredientOut]
    total: int
    page: int
    size: int
    unlinked: int = Field(description="Ingredients of the shown branches that have no catalog entry yet")


class OptionOut(BaseModel):
    id: str
    name: str


class IngredientOptionsOut(BaseModel):
    categories: list[OptionOut]
    units: list[OptionOut]


class ImpactOut(BaseModel):
    recipes: int = Field(description="Recipe lines, variant and extra lines included, that disappear with the ingredient")
    movements: int = Field(description="Stock movements that disappear with the ingredient")


class IngredientEverywhereOut(BaseModel):
    created: list[IngredientOut]
    skipped: list[str] = Field(description="Branches that already had the ingredient and were left as they were")


class CatalogLinkIn(BaseModel):
    """Link to an existing catalog entry, or make one from the ingredient's own name and unit; exactly one of the two."""

    catalog_id: str | None = None
    create_new: bool = False


class CatalogEntryOut(BaseModel):
    id: str
    name: str
    unit: str | None
    branch_count: int
