from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    station: Mapped[str | None] = mapped_column(String(10), nullable=True)
    station_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Hanya catatan pesanan yang punya cabang; kosong berarti catatan umum lama yang berlaku di semua cabang.
    outlet_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Hanya diisi untuk catatan pesanan yang dibuat v2; catatan lama tidak tahu pembuatnya.
    created_by_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Hanya kategori kode shift: jenisnya (work atau off) dan rentang jam mulai yang diizinkan, diisi admin; kosong berarti tidak ada pemeriksaan.
    shift_kind: Mapped[str | None] = mapped_column(Text, nullable=True)
    shift_start_from: Mapped[str | None] = mapped_column(Text, nullable=True)
    shift_start_until: Mapped[str | None] = mapped_column(Text, nullable=True)


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
