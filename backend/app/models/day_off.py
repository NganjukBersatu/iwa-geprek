from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


class DayOff(Base):
    __tablename__ = "day_offs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date)
    user_id: Mapped[str] = mapped_column(String)
    shift_code_id: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped[User] = relationship(User, primaryjoin="foreign(DayOff.user_id) == User.id", lazy="selectin")
