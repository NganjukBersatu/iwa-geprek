import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import ARRAY, Date, DateTime, Enum as SAEnum, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MoneySubject(str, enum.Enum):
    """The values are the labels of the CHECK constraint on money_changes.subject."""

    ORDER = "order"
    EXPENSE = "expense"
    OVERPAYMENT = "overpayment"
    SESSION = "session"


class MoneyAction(str, enum.Enum):
    """The values are the labels of the CHECK constraint on money_changes.action."""

    LATE = "late"
    UPDATE = "update"
    VOID = "void"
    UNVOID = "unvoid"
    DELETE = "delete"
    MOVE_OUT = "move_out"
    MOVE_IN = "move_in"


def _labels(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class MoneyChange(Base):
    # Baris hanya dibuat trigger database dari migrasi c3e5a7b9d104, tidak pernah oleh aplikasi.

    __tablename__ = "money_changes"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(Text)
    business_day: Mapped[date] = mapped_column(Date)
    subject: Mapped[MoneySubject] = mapped_column(SAEnum(MoneySubject, native_enum=False, values_callable=_labels, create_constraint=False))
    subject_id: Mapped[str] = mapped_column(Text)
    session_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Copied when the change happens (receipt number, item name, method, shift code), so a deleted row stays readable.
    subject_label: Mapped[str] = mapped_column(Text)
    action: Mapped[MoneyAction] = mapped_column(SAEnum(MoneyAction, native_enum=False, values_callable=_labels, create_constraint=False))
    amount_before: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_after: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fields: Mapped[list[str]] = mapped_column(ARRAY(Text))
    # Empty when the change came without a v2 account, such as from the legacy backend.
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
