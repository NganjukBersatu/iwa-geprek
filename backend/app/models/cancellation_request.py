import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CancellationStatus(str, enum.Enum):
    """The values are the labels of the existing database enum; whether a request still waits is read from `decided_at`, never from these."""

    PENDING = "menunggu"
    APPROVED = "disetujui"
    REJECTED = "ditolak"


def _labels(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class CancellationRequest(Base):
    """A request to void an order; while it waits for a decision the order is locked from other changes."""

    __tablename__ = "cancellation_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(String)
    outlet_id: Mapped[str] = mapped_column(String)
    requested_by_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CancellationStatus] = mapped_column(
        SAEnum(CancellationStatus, name="cancellation_request_status", values_callable=_labels, create_type=False),
        default=CancellationStatus.PENDING,
    )
    decided_by_id: Mapped[str | None] = mapped_column(String, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manager_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
