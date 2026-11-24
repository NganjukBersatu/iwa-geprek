from datetime import date
from decimal import Decimal

from web.management.reports.sales.response import ResponseModel
from web.management.reports.sales.trend.domain import Period


class TrendPointOut(ResponseModel):
    label: str
    start: date
    end: date
    income: Decimal
    expense: Decimal
    gross_profit: Decimal
    order_count: int
    average_transaction: Decimal
    customers: int
    new_customers: int
    returning_customers: int


class WindowOut(ResponseModel):
    """The days a dashboard period covers; it carries no figure, so whoever may open the dashboard may ask for it."""

    period: Period
    start: date
    end: date


class TrendOut(ResponseModel):
    """`period` is the bar unit actually used, which a free range chooses from its length."""

    period: Period
    start: date
    end: date
    points: list[TrendPointOut]
