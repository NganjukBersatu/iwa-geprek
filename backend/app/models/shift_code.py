from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.category import Category


class ShiftCode(Base):
    __tablename__ = "shift_codes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    # Shared by the "same" code across branches, so cross-branch reports need not match on text.
    master_id: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str] = mapped_column(String(20))
    start_clock: Mapped[str | None] = mapped_column(String(5), nullable=True)
    end_clock: Mapped[str | None] = mapped_column(String(5), nullable=True)
    color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overtime_start_clock: Mapped[str | None] = mapped_column(String(5), nullable=True)
    overtime_end_clock: Mapped[str | None] = mapped_column(String(5), nullable=True)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    is_day_off: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    category: Mapped[Category | None] = relationship(
        Category, primaryjoin="foreign(ShiftCode.category_id) == Category.id", lazy="selectin"
    )
