"""Turns the daily overview into its response schema."""
from web.management.reports.sales.daily_overview.domain import DailyOverview
from web.management.reports.sales.daily_overview.schemas import DailyOverviewOut


def daily_overview_out(overview: DailyOverview) -> DailyOverviewOut:
    return DailyOverviewOut.model_validate(overview)
