from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean)
    has_temperature_variant: Mapped[bool] = mapped_column(Boolean, default=False)
    outlet_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tax_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    service_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    # Terisi berarti menu tanpa resep dengan harga pokok segitu; kosong berarti resep atau stok terlacak, dan nol sah.
    fixed_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class MenuOutletCost(Base):
    """A branch's own fixed cost for a menu, overriding MenuItem.fixed_cost there; ignored while the menu has no fixed cost."""

    __tablename__ = "menu_outlet_costs"

    menu_item_id: Mapped[str] = mapped_column(Text, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class MenuOutletUnavailable(Base):
    """A branch's own mark that a menu is out there; MenuItem.is_available still switches the menu off at every branch."""

    __tablename__ = "menu_outlet_unavailable"

    menu_item_id: Mapped[str] = mapped_column(Text, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class MenuOutletPrice(Base):
    """A branch price for a menu item, overriding MenuItem.price there."""

    __tablename__ = "menu_outlet_prices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    menu_item_id: Mapped[str] = mapped_column(String)
    outlet_id: Mapped[str] = mapped_column(String)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Dibaca halaman perangkat untuk menilai apakah perangkat cabang ini sudah menerima harga terbaru.
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
