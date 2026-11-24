from datetime import date

from sqlalchemy import Date, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReceiptCounter(Base):
    """The last receipt sequence used by one branch on one day; no history, only the latest number."""

    __tablename__ = "receipt_counters"
    __table_args__ = (PrimaryKeyConstraint("outlet_id", "day"),)

    outlet_id: Mapped[str] = mapped_column(String)
    day: Mapped[date] = mapped_column(Date)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
