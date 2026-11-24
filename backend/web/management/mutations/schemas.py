from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class MutationRowOut(BaseModel):
    session_id: str
    cashier_username: str
    shift_code: str | None
    opened_at: datetime
    closed_at: datetime | None
    closed: bool
    planned_float: Decimal
    planned_shopping: Decimal
    cash_revenue: Decimal
    non_cash_revenue: Decimal
    drawer_expenses: Decimal
    shopping_fund_used: Decimal
    other_fund_expenses: Decimal
    # Every purchase of the session, from the drawer, the shopping fund and other funds.
    spending: Decimal
    expected_revenue: Decimal
    # Empty while the session is still open.
    actual_float: Decimal | None
    actual_shopping: Decimal | None
    actual_revenue: Decimal | None
    float_difference: Decimal | None
    shopping_difference: Decimal | None
    revenue_difference: Decimal | None


class MutationSummaryOut(BaseModel):
    sessions: int
    closed: int
    cash_revenue: Decimal
    non_cash_revenue: Decimal
    drawer_expenses: Decimal
    shopping_fund_used: Decimal
    other_fund_expenses: Decimal
    float_difference: Decimal
    shopping_difference: Decimal
    revenue_difference: Decimal


class MutationPageOut(BaseModel):
    start: date
    end: date
    items: list[MutationRowOut]
    total: int
    page: int
    size: int
    summary: MutationSummaryOut


class MoneyEventOut(BaseModel):
    at: datetime
    kind: Literal["open", "expense", "close"]
    description: str | None
    fund_source: str | None
    amount: Decimal


class MutationDetailOut(BaseModel):
    session: MutationRowOut
    events: list[MoneyEventOut]
