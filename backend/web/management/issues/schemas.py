from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from web.management.issues.domain import IssueKind, IssueLevel


class IssueOut(BaseModel):
    kind: IssueKind
    level: IssueLevel
    outlet_id: str | None
    outlet_name: str | None
    subject_id: str | None
    subject: str
    subject_kind: str | None
    day: date | None
    at: datetime | None
    amount: Decimal | None
    compared: Decimal | None
    percent: Decimal | None
    unit: str | None
    count: int | None
    days: Decimal | None


class IssuesOut(BaseModel):
    problem: int
    warning: int
    notice: int
    suggestion: int
    items: list[IssueOut]
