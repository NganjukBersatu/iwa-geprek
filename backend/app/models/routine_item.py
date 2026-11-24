from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RoutineItem(Base):
    """A purchase that repeats on a cycle; its next due date follows the last purchase still on record."""

    __tablename__ = "routine_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    cycle_days: Mapped[int] = mapped_column(Integer)
    last_purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
