"""Turns the low stock items into their response schema."""
from web.management.reports.inventory.low_stock.domain import LowStockItem
from web.management.reports.inventory.low_stock.schemas import LowStockItemOut, LowStockOut


def low_stock_out(items: list[LowStockItem]) -> LowStockOut:
    return LowStockOut(count=len(items), items=[LowStockItemOut(**vars(item)) for item in items])
