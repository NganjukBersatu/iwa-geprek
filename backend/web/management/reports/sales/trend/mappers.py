"""Turns the trend into its response schema."""
from web.management.reports.sales.trend.domain import Trend
from web.management.reports.sales.trend.schemas import TrendOut


def trend_out(trend: Trend) -> TrendOut:
    return TrendOut.model_validate(trend)
