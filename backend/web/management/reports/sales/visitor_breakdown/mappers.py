"""Turns the visitor breakdown into its response schema."""
import re
from collections.abc import Callable

from app.core.sorting import RowSorting, SortValue
from web.management.reports.sales.visitor_breakdown.domain import VisitorBreakdown, VisitorDay, VisitorGroup
from web.management.reports.sales.visitor_breakdown.schemas import VisitorBreakdownOut

GROUP_SORTING: RowSorting[VisitorGroup] = RowSorting(
    keys={
        "label": lambda row: row.label,
        "transactions": lambda row: row.transactions,
        "revenue": lambda row: row.revenue,
    },
    identity=lambda row: row.label,
)


GROUP_COLUMN = re.compile(r"^-?(gender|category)_(\d{1,3})$")


def _day_sorting(genders: list[str], categories: list[str], sort: str | None) -> RowSorting[VisitorDay]:
    """Group columns are named by position, since free-text labels cannot be a sort key; a position past the labels reads as zeros."""
    keys: dict[str, Callable[[VisitorDay], SortValue | None]] = {
        "date": lambda row: row.date,
        "transactions": lambda row: row.transactions,
        "revenue": lambda row: row.revenue,
        "average": lambda row: row.average_transaction,
    }
    for index, label in enumerate(genders):
        keys[f"gender_{index}"] = _count_of("genders", label)
    for index, label in enumerate(categories):
        keys[f"category_{index}"] = _count_of("categories", label)
    asked = GROUP_COLUMN.fullmatch(sort or "")
    if asked and asked.group(0).lstrip("-") not in keys:
        keys[asked.group(0).lstrip("-")] = lambda row: 0
    return RowSorting(keys=keys, identity=lambda row: row.date.isoformat())


def _count_of(field: str, label: str) -> Callable[[VisitorDay], SortValue | None]:
    def read(row: VisitorDay) -> SortValue:
        return getattr(row, field).get(label, 0)

    return read


def visitor_breakdown_out(breakdown: VisitorBreakdown, sort: str | None, gender_sort: str | None, category_sort: str | None) -> VisitorBreakdownOut:
    """Days and labels keep their own order for the chart; the tables come in the order each one asked for, newest day first by default."""
    genders = [group.label for group in breakdown.by_gender]
    categories = [group.label for group in breakdown.by_category]
    table = list(reversed(breakdown.days)) if sort is None else _day_sorting(genders, categories, sort).apply(breakdown.days, sort)
    return VisitorBreakdownOut.model_validate(
        {
            **breakdown.__dict__,
            "by_category": GROUP_SORTING.apply(breakdown.by_category, category_sort),
            "by_gender": GROUP_SORTING.apply(breakdown.by_gender, gender_sort),
            "category_labels": categories,
            "gender_labels": genders,
            "table": table,
        }
    )
