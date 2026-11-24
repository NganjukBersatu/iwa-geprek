"""Turns the turnover report into its response schema."""
from dataclasses import asdict

from web.management.reports.inventory.stock_turnover.domain import TurnoverReport
from web.management.reports.inventory.stock_turnover.schemas import TurnoverOut, TurnoverRowOut


def turnover_out(report: TurnoverReport) -> TurnoverOut:
    return TurnoverOut(
        start=report.start,
        end=report.end,
        days=report.days,
        **asdict(report.thresholds),
        total_stock_value=report.total_stock_value,
        out_count=report.out_count,
        urgent_count=report.urgent_count,
        dormant_count=report.dormant_count,
        dormant_value=report.dormant_value,
        total_suggested_purchase=report.total_suggested_purchase,
        rows=[TurnoverRowOut(**vars(row)) for row in report.rows],
    )
