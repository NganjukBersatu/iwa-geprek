import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


class LeaveType(str, enum.Enum):
    """The values are the labels of the existing database enum."""

    PERMIT = "izin"
    SICK = "sakit"


class LeaveStatus(str, enum.Enum):
    """The values are the labels of the existing database enum."""

    PENDING = "menunggu"
    APPROVED = "disetujui"
    REJECTED = "ditolak"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _labels(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[str] = mapped_column(String)
    type: Mapped[LeaveType] = mapped_column(
        SAEnum(LeaveType, name="leave_request_kind", values_callable=_labels, create_type=False)
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(String)
    status: Mapped[LeaveStatus] = mapped_column(
        SAEnum(LeaveStatus, name="leave_request_status", values_callable=_labels, create_type=False),
        default=LeaveStatus.PENDING,
    )
    decided_by_id: Mapped[str | None] = mapped_column(String, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manager_note: Mapped[str | None] = mapped_column(String, nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String, nullable=True)
    attachment_link: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    decided_by: Mapped[User | None] = relationship(
        User, primaryjoin="foreign(LeaveRequest.decided_by_id) == User.id", lazy="selectin"
    )
