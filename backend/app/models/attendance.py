import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, Float, Integer, String, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AttendanceStatus(str, enum.Enum):
    """The values are the labels of the existing database enum."""

    PRESENT = "hadir"
    LATE = "telat"
    PERMIT = "izin"
    SICK = "sakit"
    ABSENT = "alfa"


PRESENT_STATUSES = frozenset({AttendanceStatus.PRESENT, AttendanceStatus.LATE})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Attendance(Base):
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date)
    shift_code_id: Mapped[str | None] = mapped_column(String, nullable=True)
    schedule_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(
            AttendanceStatus,
            name="attendance_status",
            values_callable=lambda members: [member.value for member in members],
            create_type=False,
        ),
        default=AttendanceStatus.PRESENT,
    )
    clock_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clock_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_closed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    notice_seen: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    outside_schedule_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    clock_in_photo_path: Mapped[str | None] = mapped_column(String, nullable=True)
    clock_in_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_in_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_in_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_in_location_mode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    clock_in_location_note: Mapped[str | None] = mapped_column(String, nullable=True)
    clock_in_distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_in_radius_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)

    clock_out_photo_path: Mapped[str | None] = mapped_column(String, nullable=True)
    clock_out_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_out_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_out_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_out_location_mode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    clock_out_location_note: Mapped[str | None] = mapped_column(String, nullable=True)
    clock_out_distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    clock_out_radius_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
