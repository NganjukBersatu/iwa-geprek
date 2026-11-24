import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


class TaskType(str, enum.Enum):
    """The values are the labels of the existing database enum."""

    ASSIGNMENT = "penugasan"
    REPORT = "laporan"


class TaskStatus(str, enum.Enum):
    """The values are the labels of the existing database enum."""

    OPEN = "belum"
    DONE = "selesai"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _labels(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="task_kind", values_callable=_labels, create_type=False)
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status", values_callable=_labels, create_type=False), default=TaskStatus.OPEN
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    assignee_id: Mapped[str] = mapped_column(String)
    creator_id: Mapped[str | None] = mapped_column(String, nullable=True)
    assignment_photo_path: Mapped[str | None] = mapped_column(String, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Pengisian tugas outlet atau rutin yang ditindaklanjuti tugas ini; kosong untuk tugas biasa.
    source_run_id: Mapped[str | None] = mapped_column(String, ForeignKey("outlet_batch_runs.id", ondelete="SET NULL"), nullable=True)
    completion_note: Mapped[str | None] = mapped_column(String, nullable=True)
    completion_photo_path: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    assignee: Mapped[User] = relationship(
        User, primaryjoin="foreign(Task.assignee_id) == User.id", lazy="selectin"
    )
    creator: Mapped[User | None] = relationship(
        User, primaryjoin="foreign(Task.creator_id) == User.id", lazy="selectin"
    )
