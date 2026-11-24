from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base


class PrinterSlot(StrEnum):
    BAR = "bar"
    KITCHEN = "kitchen"


class DeviceSlot(StrEnum):
    RECEIPT = "receipt"
    BAR = "bar"
    KITCHEN = "kitchen"
    STATION = "station"


class PrinterConnection(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


# Daftar milik cabang, bukan tablet atau mesin printernya, supaya tetap utuh saat tablet dicabut atau printer diganti.
class PrinterCategory(Base):
    __tablename__ = "printer_categories"

    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    category_id: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    printer_slot: Mapped[PrinterSlot] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)


# Laporan tablet tentang printer yang terpasang; slot tanpa baris berarti belum dipasang.
class DevicePrinter(Base):
    __tablename__ = "device_printers"

    id: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("gen_random_uuid()::text"))
    device_id: Mapped[str] = mapped_column(Text)
    printer_slot: Mapped[DeviceSlot] = mapped_column(Text)
    # Terisi hanya untuk slot station: printer milik stasiun itu; slot station tanpa stasiun berasal dari APK lama.
    station_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    printer_name: Mapped[str] = mapped_column(Text)
    printer_address: Mapped[str] = mapped_column(Text)
    connection: Mapped[PrinterConnection] = mapped_column(Text)
