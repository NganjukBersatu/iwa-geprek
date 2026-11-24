import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum as SAEnum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.business_day import business_day_column


class FundSource(str, enum.Enum):
    """The values are the labels of the existing database enum."""

    DRAWER_CASH = "kas_laci"
    OTHER_FUNDS = "dana_lain"
    SHOPPING_FUND = "uang_belanja"


def _labels(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class Expense(Base):
    """A purchase recorded by a cashier; the fund source says whether it left the drawer."""

    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    cash_session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cashier_id: Mapped[str] = mapped_column(String)
    routine_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    item_name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fund_source: Mapped[FundSource] = mapped_column(
        SAEnum(FundSource, name="funding_source", values_callable=_labels, create_type=False)
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    buyer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    receipt_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # A line that names one of the branch's ingredients; money only, the stock never follows it.
    ingredient_id: Mapped[str | None] = mapped_column(String, nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    unit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    business_day: Mapped[date] = business_day_column()
