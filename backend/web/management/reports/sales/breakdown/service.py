"""Builds the sales breakdown: sold orders split by order type and, across all branches, by branch."""
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.orders import order_types
from app.models.outlet import Outlet
from web.management.reports.common import divide, from_today, percent
from web.management.reports.sales.breakdown import repository
from web.management.reports.sales.breakdown.domain import BreakdownRow, SalesBreakdown

UNKNOWN_KEY = "unknown"
TYPE_LABELS = {**order_types.LABELS, UNKNOWN_KEY: order_types.UNKNOWN_LABEL}


def _fold_unknown_types(grouped: dict[str, tuple[int, Decimal]]) -> dict[str, tuple[int, Decimal]]:
    """Every code outside the known labels becomes one row, so the screen never shows a raw code."""
    folded: dict[str, tuple[int, Decimal]] = {}
    for key, (count, sales) in grouped.items():
        target = key if key in order_types.LABELS else UNKNOWN_KEY
        before_count, before_sales = folded.get(target, (0, Decimal("0")))
        folded[target] = (before_count + count, before_sales + sales)
    return folded


def _rows(
    grouped: dict[str, tuple[int, Decimal]],
    label_of: dict[str, str],
    profit: dict[str, Decimal | None],
) -> list[BreakdownRow]:
    total = sum((sales for _, sales in grouped.values()), Decimal("0"))
    rows = [
        BreakdownRow(
            key=key,
            # A type or branch the labels do not know still keeps its row: its sales were real.
            label=label_of.get(key, key),
            transaction_count=count,
            sales_total=sales,
            average_per_transaction=divide(sales, count),
            sales_percent=percent(sales, total),
            gross_profit=profit.get(key),
        )
        for key, (count, sales) in grouped.items()
    ]
    rows.sort(key=lambda row: (-row.sales_total, row.label))
    return rows


def sales_breakdown(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> SalesBreakdown:
    """By order type for the chosen scope; by branch only when no branch is chosen."""
    start, end = from_today(start, end)
    by_type = _rows(_fold_unknown_types(repository.sales_by_order_type(db, start, end, outlet_id)), TYPE_LABELS, {})
    if outlet_id is not None:
        return SalesBreakdown(start=start, end=end, order_types=by_type, outlets=[])

    grouped = repository.sales_by_outlet(db, start, end)
    names = dict(db.execute(select(Outlet.id, Outlet.name).where(Outlet.id.in_(grouped))).all()) if grouped else {}
    by_outlet = _rows(grouped, names, repository.line_profit_by_outlet(db, start, end))
    return SalesBreakdown(start=start, end=end, order_types=by_type, outlets=by_outlet)
