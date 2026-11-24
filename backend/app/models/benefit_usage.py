from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BenefitUsage(Base):
    """A partner benefit used on one order; its amount is billed to the partner."""

    __tablename__ = "benefit_usages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_id: Mapped[str] = mapped_column(String)
    employee_id: Mapped[str] = mapped_column(String)
    order_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    used_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    menu_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
