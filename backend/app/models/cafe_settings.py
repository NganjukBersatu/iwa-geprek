from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base


class CafeSettings(Base):
    __tablename__ = "cafe_settings"

    outlet_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    complaint_number: Mapped[str] = mapped_column(String(40), default="")
    wifi: Mapped[list] = mapped_column(JSON, default=list)
    wifi_password: Mapped[str] = mapped_column(String(120), default="")
    social: Mapped[list] = mapped_column(JSON, default=list)
    receipt_greeting: Mapped[str] = mapped_column(String(200), default="")
    # Serving stages of the branch board; empty means the default pair, see app.core.orders.stages.
    order_stages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    late_tolerance_minutes: Mapped[int] = mapped_column(Integer)
    late_penalty_per_minute: Mapped[int] = mapped_column(Integer)
    auto_close_after_hours: Mapped[int] = mapped_column(Integer)
    cost_markup_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    target_margin_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    service_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
