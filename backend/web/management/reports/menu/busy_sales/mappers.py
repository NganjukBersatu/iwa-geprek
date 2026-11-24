"""Turns the busy-sales report into its response schema."""
from app.core.sorting import RowSorting
from web.management.reports.menu.busy_sales.domain import BusySales, BusySalesRow
from web.management.reports.menu.busy_sales.schemas import BusySalesOut, BusySalesRowOut
from web.management.reports.menu.highlights import highlight_out


def _row_out(row: BusySalesRow) -> BusySalesRowOut:
    fields = {name: value for name, value in vars(row).items() if name != "slot"}
    return BusySalesRowOut(key=row.slot.key, label=row.slot.label, occurrences=row.slot.occurrences, **fields)


def _sorting(rows: list[BusySalesRow]) -> RowSorting[BusySalesRow]:
    position = {row.slot.key: index for index, row in enumerate(rows)}
    return RowSorting(
        keys={
            "time": lambda row: position[row.slot.key],
            "sales": lambda row: row.sales,
            "transactions": lambda row: row.transactions,
            "products": lambda row: row.products,
            "customers": lambda row: row.customers,
        },
        identity=lambda row: f"{position[row.slot.key]:06d}",
    )


def busy_sales_out(report: BusySales, sort: str | None) -> BusySalesOut:
    fields = {name: value for name, value in vars(report).items() if name not in ("highlights", "rows")}
    rows = [_row_out(row) for row in report.rows]
    by_key = {row.key: row for row in rows}
    return BusySalesOut(
        **fields,
        highlights=[highlight_out(item) for item in report.highlights],
        rows=rows,
        table=[by_key[row.slot.key] for row in _sorting(report.rows).apply(report.rows, sort)],
    )
