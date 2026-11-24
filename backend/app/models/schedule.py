from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.role import Role
from app.models.shift_code import ShiftCode
from app.models.user import User


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date)
    user_id: Mapped[str] = mapped_column(String)
    shift_code_id: Mapped[str | None] = mapped_column(String, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    role_id: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    # Set once by the first clock-in on this assignment; the single mark that an assignment is used.
    clock_in_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    user: Mapped[User] = relationship(User, primaryjoin="foreign(Schedule.user_id) == User.id", lazy="selectin")
    role: Mapped[Role | None] = relationship(Role, primaryjoin="foreign(Schedule.role_id) == Role.id", lazy="selectin")
    shift_code: Mapped[ShiftCode | None] = relationship(
        ShiftCode, primaryjoin="foreign(Schedule.shift_code_id) == ShiftCode.id", lazy="selectin"
    )
