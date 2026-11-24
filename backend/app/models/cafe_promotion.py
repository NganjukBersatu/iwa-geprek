from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base

UPLOAD_FOLDER = "promosi"


class CafePromotion(Base):
    """An announcement of the cafe, such as an event or a banner; it never changes a price."""

    __tablename__ = "cafe_promotions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    # Either an uploaded file under UPLOAD_FOLDER or a link pasted from elsewhere.
    image: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean)
    # Kosong berlaku di semua cabang; terisi milik satu cabang itu saja.
    outlet_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
