import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OutletTask(Base):
    """A task owned by a branch instead of a person; anyone at the branch may finish it, once."""

    __tablename__ = "outlet_tasks"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creator_id: Mapped[str | None] = mapped_column(String, nullable=True)
    completer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    completion_note: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    creator: Mapped[User | None] = relationship(
        User, primaryjoin="foreign(OutletTask.creator_id) == User.id", lazy="selectin"
    )
    completer: Mapped[User | None] = relationship(
        User, primaryjoin="foreign(OutletTask.completer_id) == User.id", lazy="selectin"
    )
