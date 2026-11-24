import uuid
from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class BranchPeriod(Base):
    """Periode tutup buku satu cabang bertanggal lengkap, disimpan bila diatur tangan; selebihnya dibentuk dari pola patokan."""

    __tablename__ = "branch_periods"
    __table_args__ = (
        UniqueConstraint("outlet_id", "start_date", name="unique_branch_periods_outlet_id_start_date"),
        CheckConstraint("end_date >= start_date", name="check_branch_periods_end_date_order"),
        CheckConstraint(
            "(pattern_start_day IS NULL AND pattern_end_day IS NULL) OR (pattern_start_day BETWEEN 1 AND 31 AND pattern_end_day BETWEEN 1 AND 31)",
            name="check_branch_periods_pattern_days",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_new_id)
    outlet_id: Mapped[str] = mapped_column(Text, ForeignKey("outlets.id", ondelete="RESTRICT"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    # Terisi berarti periode ini patokan: bulan-bulan sesudahnya yang belum tersimpan mengikuti tanggal mulai dan akhir ini.
    pattern_start_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pattern_end_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
