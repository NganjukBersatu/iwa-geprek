import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base


class NonCashCheck(Base):
    """The real non-cash figure from the bank app, typed by an admin for one branch on one day, for audit only."""

    __tablename__ = "non_cash_checks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date)
    bank_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    entered_by: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
