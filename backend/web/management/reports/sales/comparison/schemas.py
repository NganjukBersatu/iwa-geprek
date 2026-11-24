from datetime import date
from decimal import Decimal

from web.management.reports.sales.comparison.domain import ComparisonMode
from web.management.reports.sales.response import ResponseModel


class MetricOut(ResponseModel):
    current: Decimal
    previous: Decimal
    difference: Decimal
    percent: Decimal | None


class ComparisonOut(ResponseModel):
    start: date
    end: date
    mode: ComparisonMode
    previous_start: date
    previous_end: date
    comparison_label: str
    cut_off_at: str | None
    income: MetricOut
    expense: MetricOut
    transactions: MetricOut
    average_transaction: MetricOut
    customers: MetricOut
    profit: MetricOut
