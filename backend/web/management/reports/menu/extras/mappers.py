"""Turns the extras report into its response schema."""
from app.core.sorting import RowSorting
from web.management.reports.menu.extras.domain import ExtraRow, Extras
from web.management.reports.menu.extras.schemas import ExtraRowOut, ExtrasOut

SORTING: RowSorting[ExtraRow] = RowSorting(
    keys={
        "extra": lambda row: row.extra,
        "quantity": lambda row: row.quantity,
        "transactions": lambda row: row.transactions,
        "revenue": lambda row: row.revenue,
        "profit": lambda row: row.profit,
    },
    identity=lambda row: row.extra,
)


def extras_out(report: Extras, sort: str | None) -> ExtrasOut:
    fields = {name: value for name, value in vars(report).items() if name != "rows"}
    return ExtrasOut(**fields, rows=[ExtraRowOut(**vars(row)) for row in SORTING.apply(report.rows, sort)])
