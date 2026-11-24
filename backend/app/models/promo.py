from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base


class Promo(Base):
    __tablename__ = "promos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[str] = mapped_column(String(16))
    discount_type: Mapped[str] = mapped_column(String(16))
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    applies_to: Mapped[str | None] = mapped_column(String(500), nullable=True)
    product_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    minimum_spend: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    activation: Mapped[str] = mapped_column(String(16))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean)
    # Kosong berlaku di semua cabang; terisi milik satu cabang itu saja.
    outlet_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    # The table has no database default for these, so a new promo must carry them.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
