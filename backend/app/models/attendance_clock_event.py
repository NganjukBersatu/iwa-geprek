import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CLOCK_IN = "clock_in"
CLOCK_OUT = "clock_out"

# Waktu absen dihitung dari jangkar waktu server, atau dari jam perangkat bila jangkarnya hilang.
SOURCE_SERVER_ANCHORED = "server_anchored"
SOURCE_DEVICE_CLOCK = "device_clock"


class AttendanceClockEvent(Base):
    """Satu absen datang atau pulang yang dikirim app; kunci idempotensinya membuat kiriman ulang tidak menggandakan absen."""

    __tablename__ = "attendance_clock_events"

    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(Text)
    attendance_id: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    time_source: Mapped[str] = mapped_column(Text)
    request_hash: Mapped[str] = mapped_column(Text)
