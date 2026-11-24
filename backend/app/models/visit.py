from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Visit(Base):
    """A customer coming to a branch, recorded by the camera or by hand."""

    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    customer_id: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String(50))
    recognition_event_id: Mapped[str | None] = mapped_column(String, nullable=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    order_note: Mapped[str | None] = mapped_column(Text, nullable=True)
