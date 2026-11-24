import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base
from app.models.business_day import business_day_column

STOCK_IN = "masuk"
STOCK_OUT = "keluar"
STOCK_ADJUSTMENT = "penyesuaian"


class StockItem(Base):
    """A resold menu item whose quantity a branch tracks."""

    __tablename__ = "stock_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    menu_item_id: Mapped[str] = mapped_column(String)
    unit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    minimum: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal(0))
    is_tracked: Mapped[bool] = mapped_column(Boolean, default=True)
    # Written only by the database triggers on kartu_stok and stok_item; the app reads it, never sets it.
    balance: Mapped[Decimal] = mapped_column(Numeric(16, 3), server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class StockCard(Base):
    """One stock movement; the item's balance moves with it through a database trigger."""

    __tablename__ = "stock_cards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    menu_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    menu_item_name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(20))
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    cost_after: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    business_day: Mapped[date] = business_day_column()
