import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class Deposit(Base):
    """Cash handed over to the owner: one event on one date that settles all or part of the cash of one or more income days."""

    __tablename__ = "deposits"
    __table_args__ = (Index("ix_deposits_outlet_date", "outlet_id", "deposit_date"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    outlet_id: Mapped[str] = mapped_column(String, ForeignKey("outlets.id", ondelete="RESTRICT"))
    deposit_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    days: Mapped[list["DepositDay"]] = relationship("DepositDay", order_by="DepositDay.day", cascade="all, delete-orphan", lazy="selectin")


class DepositDay(Base):
    """How much of one income day a deposit settled; a day settled in steps has several of these."""

    __tablename__ = "deposit_days"
    __table_args__ = (UniqueConstraint("deposit_id", "day", name="uq_deposit_days_deposit_day"), Index("ix_deposit_days_day", "day"))

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    deposit_id: Mapped[str] = mapped_column(String, ForeignKey("deposits.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
