from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PrintMode(StrEnum):
    CASHIER = "cashier"
    STATION = "station"


class Outlet(Base):
    __tablename__ = "outlets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    receipt_number: Mapped[str | None] = mapped_column(String(8), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    attendance_radius_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    google_review_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_location_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    print_mode: Mapped[PrintMode] = mapped_column(Text, default=PrintMode.CASHIER, server_default=PrintMode.CASHIER.value)
    cash_float: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    spending_float: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Terisi sejak penghapusan permanen dimulai; cabang setengah terhapus tidak boleh dibuka kembali.
    removal_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
