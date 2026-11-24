from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VariantGroup(Base):
    """A set of variants such as hot or ice; a required group needs exactly one choice on every order line."""

    __tablename__ = "variant_groups"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    required: Mapped[bool] = mapped_column(Boolean)
    position: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean)
    # Kosong berlaku di semua cabang; terisi milik satu cabang itu saja.
    outlet_id: Mapped[str | None] = mapped_column(Text, nullable=True)


class VariantChoice(Base):
    """One choice inside a group; it never changes the price."""

    __tablename__ = "variant_choices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    group_id: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String(60))
    color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    position: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean)


class MenuVariantGroup(Base):
    """Which menu items use a variant group."""

    __tablename__ = "menu_variant_groups"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    menu_item_id: Mapped[str] = mapped_column(String)
    group_id: Mapped[str] = mapped_column(String)


class VariantChoiceRecipe(Base):
    """Ingredient a variant choice uses at a branch, on top of the menu item's own recipe."""

    __tablename__ = "variant_choice_recipes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    choice_id: Mapped[str] = mapped_column(String)
    outlet_id: Mapped[str] = mapped_column(String)
    ingredient_id: Mapped[str] = mapped_column(String)
    catalog_id: Mapped[str | None] = mapped_column(String, nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3))
