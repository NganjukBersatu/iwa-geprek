"""Turns the profit and loss report into its response schema."""
from web.management.reports.sales.profit_loss.domain import ProfitLoss
from web.management.reports.sales.profit_loss.schemas import ProfitLossOut


def profit_loss_out(report: ProfitLoss) -> ProfitLossOut:
    return ProfitLossOut.model_validate(report)
