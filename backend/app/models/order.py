from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.business_day import business_day_column

CASH_METHOD = "tunai"


class Order(Base):
    """A cashier transaction of the legacy backend; v2 only reads it."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    cash_session_id: Mapped[str] = mapped_column(String)
    outlet_id: Mapped[str] = mapped_column(String)
    cashier_id: Mapped[str] = mapped_column(String)
    customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    table_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_type: Mapped[str] = mapped_column(String(16))
    visitor_category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    visitor_category_label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    visitor_gender_id: Mapped[str | None] = mapped_column(String, nullable=True)
    visitor_gender_label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    note_id: Mapped[str | None] = mapped_column(String, nullable=True)
    note_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receipt_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # The tablet's idempotency key: sending the same order twice returns the first one.
    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    payment_method_label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payment_method_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cash_received: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    promo_id: Mapped[str | None] = mapped_column(String, nullable=True)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    partner_covered: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), server_default=text("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    business_day: Mapped[date] = business_day_column()
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voided_by_id: Mapped[str | None] = mapped_column(String, nullable=True)
    serving_status: Mapped[str] = mapped_column(String(16))
    served_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # An open bill is written and sent to the stations before it is paid; reports and session totals skip it until it is settled.
    is_open: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Rises with every change of an open bill; a payer sends the version it saw, so a stale total is refused.
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    settle_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    @classmethod
    def is_cash(cls):
        """Orders without a method predate the column, when every sale was cash."""
        return (cls.payment_method == CASH_METHOD) | cls.payment_method.is_(None)
