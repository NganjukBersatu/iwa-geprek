"""Turns the variants report into its response schema."""
from app.core.sorting import RowSorting
from web.management.reports.menu.variants.domain import VariantRow, Variants
from web.management.reports.menu.variants.schemas import VariantRowOut, VariantsOut

SORTING: RowSorting[VariantRow] = RowSorting(
    keys={
        "option": lambda row: row.option,
        "portions": lambda row: row.portions,
        "revenue": lambda row: row.revenue,
        "margin": lambda row: row.margin,
    },
    identity=lambda row: f"{row.option}|{row.menu or ''}",
)


def _sorted(rows: list[VariantRow], sort: str | None) -> list[VariantRow]:
    """Each group is ordered on its own, and the groups keep their place."""
    groups: dict[str, list[VariantRow]] = {}
    for row in rows:
        groups.setdefault(row.group, []).append(row)
    return [row for members in groups.values() for row in SORTING.apply(members, sort)]


def variants_out(report: Variants, sort: str | None) -> VariantsOut:
    return VariantsOut(
        start=report.start,
        end=report.end,
        by_menu=report.by_menu,
        rows=[VariantRowOut(**vars(row)) for row in _sorted(report.rows, sort)],
    )
