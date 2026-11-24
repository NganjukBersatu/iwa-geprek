import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

KIND_PHOTO = "photo"
KIND_VIDEO = "video"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskAttachment(Base):
    """A photo or video of a task; exactly one of the two owner columns is set."""

    __tablename__ = "task_attachments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    personal_task_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    outlet_task_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    kind: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(500))
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_by_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
