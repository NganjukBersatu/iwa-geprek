"""Turns the ingredient stock report into its response schema."""
from web.management.reports.inventory.ingredient_stock.domain import StockReport
from web.management.reports.inventory.ingredient_stock.schemas import IngredientStockOut, IngredientStockRowOut


def ingredient_stock_out(report: StockReport) -> IngredientStockOut:
    return IngredientStockOut(
        start=report.start,
        end=report.end,
        count_id=report.count_id,
        total_replacement=report.total_replacement,
        total_tolerated_value=report.total_tolerated_value,
        check_count=report.check_count,
        rows=[IngredientStockRowOut(**vars(row)) for row in report.rows],
    )
