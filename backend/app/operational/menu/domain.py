from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from app.core.catalog.selling import ExtraOption, VariantOptions
from app.models.menu_item import MenuItem


@dataclass(frozen=True)
class MenuView:
    item: MenuItem
    selling_price: Decimal
    category_name: str | None
    ready_to_sell: bool
    # Ditandai habis oleh cabang pembaca; saklar menu di semua cabang ada di item.is_available.
    marked_out_here: bool = False
    missing_ingredients: list[str] = field(default_factory=list)


class CostBasis(StrEnum):
    """Dari mana harga pokok menu dihitung di cabang; nilainya kontrak API untuk tablet."""

    FIXED = "fixed"
    RECIPE = "recipe"
    RESALE = "resale"
    NONE = "none"


@dataclass(frozen=True)
class RecipeStock:
    """Satu bahan resep menu beserta stok cabang saat ini."""

    ingredient_name: str
    unit: str | None
    qty: Decimal
    stock: Decimal


@dataclass(frozen=True)
class MenuDetail:
    view: MenuView
    variant_groups: list[VariantOptions]
    extras: list[ExtraOption]
    recipe: list[RecipeStock] | None
    portions_left: int | None
    maker_station: str | None
    sold_today: int
    cost_basis: CostBasis


@dataclass(frozen=True)
class MenuPage:
    items: list[MenuView]
    total: int
    page: int
    size: int
