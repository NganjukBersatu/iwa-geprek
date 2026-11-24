from datetime import date
from decimal import Decimal

from web.management.reports.sales.response import ResponseModel


class VisitorGroupOut(ResponseModel):
    label: str
    transactions: int
    revenue: Decimal
    percent: Decimal


class VisitorDayOut(ResponseModel):
    date: date
    transactions: int
    revenue: Decimal
    average_transaction: Decimal
    categories: dict[str, int]
    genders: dict[str, int]


class VisitorBreakdownOut(ResponseModel):
    start: date
    end: date
    total_transactions: int
    total_revenue: Decimal
    with_category: int
    with_gender: int
    by_category: list[VisitorGroupOut]
    by_gender: list[VisitorGroupOut]
    category_labels: list[str]
    gender_labels: list[str]
    days: list[VisitorDayOut]
    # The same days in the order the table asked for, while `days` keeps the date axis the chart draws.
    table: list[VisitorDayOut]
