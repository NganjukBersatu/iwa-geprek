import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum as SAEnum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.business_day import business_day_column


class CashSessionStatus(str, enum.Enum):
    """The values are the labels of the existing database enum."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


def _labels(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class CashSession(Base):
    """A cashier's till session, called a shift in the legacy backend; v2 only reads it."""

    __tablename__ = "cash_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    cashier_id: Mapped[str] = mapped_column(String)
    shift_code_id: Mapped[str | None] = mapped_column(String, nullable=True)
    shift_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shift_code_color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    business_day: Mapped[date] = business_day_column()
    opening_cash: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    system_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cash_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    drawer_expenses: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    actual_cash: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    difference: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    planned_float: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    planned_shopping: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    actual_float: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    actual_shopping: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    actual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[CashSessionStatus] = mapped_column(
        SAEnum(CashSessionStatus, name="cash_session_status", values_callable=_labels, create_type=False)
    )
