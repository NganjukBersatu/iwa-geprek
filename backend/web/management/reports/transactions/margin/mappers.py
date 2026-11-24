"""Turns the margin report into its response schema."""
from dataclasses import asdict

from app.core.sorting import RowSorting
from web.management.reports.transactions.margin.domain import MarginReport, MenuMargin
from web.management.reports.transactions.margin.schemas import MarginOut, MenuMarginOut


TOP_MENUS = 10

SORTING: RowSorting[MenuMargin] = RowSorting(
    keys={
        "menu": lambda item: item.menu_item_name,
        "qty": lambda item: item.qty,
        "revenue": lambda item: item.revenue,
        "cost": lambda item: item.cost,
        "margin": lambda item: item.margin,
        "margin_percent": lambda item: item.margin_percent,
    },
    identity=lambda item: f"{item.menu_item_name}|{item.menu_item_id or ''}",
)


def margin_out(report: MarginReport, sort: str | None) -> MarginOut:
    """Items arrive by revenue, largest first, so the chart's top menus never follow the table's order."""
    return MarginOut(
        start=report.start,
        end=report.end,
        items=[MenuMarginOut(**asdict(item)) for item in SORTING.apply(report.items, sort)],
        top=[MenuMarginOut(**asdict(item)) for item in report.items[:TOP_MENUS]],
        total_revenue=report.total_revenue,
        total_cost=report.total_cost,
        total_margin=report.total_margin,
        menus_without_cost=report.menus_without_cost,
        orders_without_lines=report.orders_without_lines,
        revenue_without_lines=report.revenue_without_lines,
    )
