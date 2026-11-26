from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base


class PaymentMethod(Base):
    """A payment method of one branch; master_id ties the same method across branches."""

    __tablename__ = "payment_methods"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    master_id: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str] = mapped_column(String(16))
    label: Mapped[str] = mapped_column(String(40))
    icon: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean)
    needs_change: Mapped[bool] = mapped_column(Boolean)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str] = mapped_column(Text)
    fee_percent: Mapped[Decimal] = mapped_column(Numeric(5, 3))
    # Dibaca halaman perangkat untuk menilai apakah perangkat cabang ini sudah menerima metode bayar terbaru.
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
