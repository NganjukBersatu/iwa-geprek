from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class SessionRowOut(BaseModel):
    id: str
    cashier_username: str
    opened_at: datetime
    closed_at: datetime | None
    revenue: Decimal
    expense: Decimal


class SessionListOut(BaseModel):
    start: date
    end: date
    total: int
    items: list[SessionRowOut]


class SessionLineOut(BaseModel):
    at: datetime
    kind: Literal["income", "expense"]
    description: str
    amount: Decimal
    quantity: int | None
    order_id: str | None


class SessionLinesOut(BaseModel):
    session_id: str
    lines: list[SessionLineOut]
