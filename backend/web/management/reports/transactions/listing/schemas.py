from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

TransactionGroup = Literal["all", "cash", "non_cash"]


class MethodTotalOut(BaseModel):
    code: str
    label: str
    count: int
    amount: Decimal


class TransactionOut(BaseModel):
    id: str
    receipt_number: str | None
    created_at: datetime
    cashier: str
    method: str
    method_label: str
    total: Decimal
    voided: bool
    table_no: str | None
    customer_name: str | None


class TransactionsOut(BaseModel):
    start: date
    end: date
    group: TransactionGroup
    method: str | None
    count: int
    amount: Decimal
    by_method: list[MethodTotalOut]
    page: int
    per_page: int
    rows: list[TransactionOut]
