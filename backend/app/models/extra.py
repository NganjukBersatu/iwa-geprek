from decimal import Decimal

from sqlalchemy import JSON, Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Extra(Base):
    """A paid add-on such as boba; price is the base price, a branch may override it."""

    __tablename__ = "extras"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    outlet_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class ExtraOutletPrice(Base):
    """A branch price for an extra, overriding Extra.price there."""

    __tablename__ = "extra_outlet_prices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    extra_id: Mapped[str] = mapped_column(String)
    outlet_id: Mapped[str] = mapped_column(String)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class MenuExtra(Base):
    """Which menu items may be given an extra."""

    __tablename__ = "menu_extras"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    menu_item_id: Mapped[str] = mapped_column(String)
    extra_id: Mapped[str] = mapped_column(String)


class ExtraRecipe(Base):
    """Ingredient an extra uses at a branch."""

    __tablename__ = "extra_recipes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    extra_id: Mapped[str] = mapped_column(String)
    outlet_id: Mapped[str] = mapped_column(String)
    ingredient_id: Mapped[str] = mapped_column(String)
    catalog_id: Mapped[str | None] = mapped_column(String, nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3))
