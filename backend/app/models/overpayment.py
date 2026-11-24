from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.business_day import business_day_column


class Overpayment(Base):
    """Money a customer paid beyond the order total by a method that gives no change."""

    __tablename__ = "overpayments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(String)
    outlet_id: Mapped[str] = mapped_column(String)
    cash_session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cashier_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cashier_name: Mapped[str] = mapped_column(String(255))
    method_code: Mapped[str] = mapped_column(String(16))
    method_label: Mapped[str] = mapped_column(String(40))
    order_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    received: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    business_day: Mapped[date] = business_day_column()
