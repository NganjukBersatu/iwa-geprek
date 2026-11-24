from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Partner(Base):
    """An organisation whose employees get a benefit at the cafe; it is switched off with is_active, never deleted."""

    __tablename__ = "partners"
    __table_args__ = (UniqueConstraint("invite_code", name="unique_partners_invite_code"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pic_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pic_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pic_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contract_start: Mapped[date] = mapped_column(Date)
    contract_end: Mapped[date] = mapped_column(Date)
    invite_code: Mapped[str] = mapped_column(String(12))
    is_active: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PartnerEmployee(Base):
    """A person of a partner and the benefit that person holds; status says whether it may be used."""

    __tablename__ = "partner_employees"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    partner_id: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employee_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flat_discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    monthly_open_table: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    monthly_quota: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(10))
    customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PartnerEmployeeFreeMenu(Base):
    """A menu item a partner employee may take free, up to a daily limit."""

    __tablename__ = "partner_employee_free_menus"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String)
    menu_item_id: Mapped[str] = mapped_column(String)
    daily_limit: Mapped[int] = mapped_column(Integer)
