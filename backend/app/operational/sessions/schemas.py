from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.finance.session_rows import SessionHistoryRowOut
from app.models.cash_session import CashSessionStatus

MAX_NOTE_LENGTH = 500


class SessionOpenIn(BaseModel):
    opening_cash: Decimal = Field(ge=0)


class SessionCloseIn(BaseModel):
    """`actual_cash` for an ordinary session; the three parts when the session holds a shopping fund."""

    actual_cash: Decimal | None = Field(None, ge=0)
    actual_float: Decimal | None = Field(None, ge=0)
    actual_shopping: Decimal | None = Field(None, ge=0)
    actual_revenue: Decimal | None = Field(None, ge=0)
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class SessionOut(BaseModel):
    id: str
    opened_at: datetime
    # The day every sale, expense, promo and receipt number of this session belongs to.
    business_day: date
    opening_cash: Decimal
    shift_code: str | None
    # Decided when the session opened: closing then asks for float, shopping fund and revenue separately.
    three_parts: bool
    planned_float: Decimal | None
    planned_shopping: Decimal | None


class RecapOut(BaseModel):
    session: SessionOut
    status: CashSessionStatus
    revenue: Decimal
    cash_revenue: Decimal
    non_cash_revenue: Decimal
    drawer_expenses: Decimal
    other_fund_expenses: Decimal
    shopping_fund_used: Decimal
    transactions: int
    voided_transactions: int
    expected_cash: Decimal
    # Three-part sessions only: cash sales less drawer and shopping-fund purchases.
    expected_revenue: Decimal
    actual_cash: Decimal | None
    difference: Decimal | None
    actual_float: Decimal | None
    actual_shopping: Decimal | None
    actual_revenue: Decimal | None
    note: str | None
    # Orders of this session still at a station; closing anyway takes them off the board.
    station_open_orders: int = 0


class MethodTotalOut(BaseModel):
    label: str
    cash: bool
    amount: Decimal
    transactions: int


class OwnSessionPageOut(BaseModel):
    items: list[SessionHistoryRowOut]
    total: int
    page: int
    size: int
