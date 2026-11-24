from decimal import Decimal

from pydantic import BaseModel, Field

MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 2000
MAX_PERCENT = 100


class MenuCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    # The base price every branch follows unless it has its own.
    price: Decimal = Field(ge=0)
    category_id: str = Field(min_length=1)
    is_available: bool = True
    # Empty sells the menu at every branch; a list limits it to those branches.
    outlet_ids: list[str] | None = None
    # {branch id: price}; on create a branch left empty simply follows the base price.
    branch_prices: dict[str, Decimal | None] | None = None
    # Empty follows the branch settings; a figure, 0 included, overrides them for this menu.
    tax_percent: Decimal | None = Field(None, ge=0, le=MAX_PERCENT)
    service_percent: Decimal | None = Field(None, ge=0, le=MAX_PERCENT)


class MenuUpdateIn(BaseModel):
    """A field left out stays as it is; tax and service sent empty go back to the branch settings."""

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    price: Decimal | None = Field(None, ge=0)
    category_id: str | None = None
    is_available: bool | None = None
    outlet_ids: list[str] | None = None
    # {branch id: price} keeps a branch price, {branch id: null} removes it; branches left out stay.
    branch_prices: dict[str, Decimal | None] | None = None
    tax_percent: Decimal | None = Field(None, ge=0, le=MAX_PERCENT)
    service_percent: Decimal | None = Field(None, ge=0, le=MAX_PERCENT)


class MenuItemOut(BaseModel):
    id: str
    name: str
    description: str | None
    price: Decimal
    category_id: str | None
    category_name: str | None
    image_url: str | None
    # Saklar menu di semua cabang; tiap cabang juga bisa menandai habis sendiri dari tabletnya.
    is_available: bool
    # Cabang yang menandai menu ini habis dari tabletnya; kosong bila tidak ada.
    unavailable_outlet_ids: list[str]
    outlet_ids: list[str] | None
    branch_prices: dict[str, Decimal]
    tax_percent: Decimal | None
    service_percent: Decimal | None
    # Only whether the menu is costed by a fixed figure; the amounts are read through the cost routes, which need their own permission, because this response is shared.
    has_fixed_cost: bool


class FixedCostIn(BaseModel):
    """A field left out stays; a figure sets it. {branch id: null} removes that branch's own cost so it follows the base."""

    cost: Decimal | None = Field(None, ge=0, lt=Decimal(100_000_000))
    branch_costs: dict[str, Decimal | None] | None = None


class FixedCostOut(BaseModel):
    # Empty means the menu has no fixed cost and is costed by its recipe or its counted stock.
    cost: Decimal | None
    branch_costs: dict[str, Decimal]


class MenuItemPageOut(BaseModel):
    items: list[MenuItemOut]
    total: int
    page: int
    size: int


class MenuCategoryOut(BaseModel):
    id: str
    name: str
