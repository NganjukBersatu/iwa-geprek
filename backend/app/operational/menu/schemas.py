from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.operational.menu.constants import MAX_DESCRIPTION_LENGTH, MAX_NAME_LENGTH


class MenuChangesIn(BaseModel):
    """Isian yang tidak dikirim tetap seperti semula."""

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    category_id: str | None = None
    is_available: bool | None = None

class AvailabilityIn(BaseModel):
    is_available: bool


class MenuOut(BaseModel):
    id: str
    name: str
    description: str | None
    # Harga jual cabang pembaca, sama dengan yang ditagih kasir.
    price: Decimal
    category_id: str | None
    category_name: str | None
    image_url: str | None
    # Tersedia di cabang pembaca: saklar menu di semua cabang menyala dan cabang ini tidak menandainya habis.
    is_available: bool
    # Dimatikan dari web admin untuk semua cabang; tablet tidak bisa menyalakannya.
    switched_off_for_all: bool
    ready_to_sell: bool
    missing_ingredients: list[str]
    # Harga pokok diketik di menu, bukan dari resep; angkanya tidak dikirim ke tablet.
    has_fixed_cost: bool


class VariantGroupDetailOut(BaseModel):
    name: str
    required: bool
    choices: list[str]


class ExtraDetailOut(BaseModel):
    name: str
    price: Decimal


class RecipeLineDetailOut(BaseModel):
    ingredient_name: str
    unit: str | None
    # Takaran satu porsi dalam satuan bahan itu sendiri.
    qty: Decimal
    # Stok cabang saat ini dalam satuan yang sama.
    stock: Decimal
    # Stok belum cukup untuk satu porsi.
    short: bool


class MenuDetailOut(BaseModel):
    menu: MenuOut
    variant_groups: list[VariantGroupDetailOut]
    extras: list[ExtraDetailOut]
    # Kosong bagi pembaca yang tidak berhak melihat Master Resep.
    recipe: list[RecipeLineDetailOut] | None
    # Porsi yang masih tercukupi stok cabang; kosong tanpa resep atau tanpa hak melihat resep.
    portions_left: int | None
    # Stasiun pembuat menu ini di cabang; kosong bila langsung diantar.
    maker_station: str | None
    # Porsi terjual pada hari bisnis ini di cabang, tanpa pesanan yang dibatalkan.
    sold_today: int
    # Dasar harga pokok: fixed, recipe, resale, atau none.
    cost_basis: Literal["fixed", "recipe", "resale", "none"]


class MenuPageOut(BaseModel):
    items: list[MenuOut]
    total: int
    page: int
    size: int


class CategoryOut(BaseModel):
    id: str
    name: str
