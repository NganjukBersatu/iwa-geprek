from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

VARIANT = "varian"
EXTRA = "ekstra"


class OrderItemOption(Base):
    """A variant or extra chosen for a sold line, copied by name at checkout."""

    __tablename__ = "order_item_options"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    order_item_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String(8))
    ref_id: Mapped[str | None] = mapped_column(String, nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    name: Mapped[str] = mapped_column(String(80))
    color: Mapped[str | None] = mapped_column(String(9), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    qty: Mapped[int] = mapped_column(Integer)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
