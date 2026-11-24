"""Turns shift code groups into response schemas."""
from app.core.sorting import RowSorting
from web.management.shift_code_groups.domain import CodeGroup
from web.management.shift_codes import clock_rules
from web.management.shift_code_groups.schemas import ShiftCodeGroupBranchOut, CodeGroupOut


SORTING: RowSorting[CodeGroupOut] = RowSorting(
    keys={
        "code": lambda row: row.code,
        "category": lambda row: row.category,
        "hours": lambda row: None if row.is_day_off else row.start_clock,
        "overtime": lambda row: row.overtime_start_clock,
        "branches": lambda row: ", ".join(branch.name for branch in row.branches),
        "assignments": lambda row: row.assignments,
    },
    identity=lambda row: row.id,
)


def sorted_groups(rows: list[CodeGroupOut], sort: str | None) -> list[CodeGroupOut]:
    """In the list's own order, groups sharing a code sit side by side so their hours can be compared; every other row keeps its place."""
    if sort is not None:
        return SORTING.apply(rows, sort)
    first: dict[str, int] = {}
    for index, row in enumerate(rows):
        first.setdefault(row.code, index)
    return sorted(rows, key=lambda row: first[row.code])


def code_group_out(group: CodeGroup) -> CodeGroupOut:
    first = group.first
    return CodeGroupOut(
        id=group.key,
        code=first.code,
        category=group.category,
        start_clock=first.start_clock,
        end_clock=first.end_clock,
        overtime_start_clock=first.overtime_start_clock,
        overtime_end_clock=first.overtime_end_clock,
        color=first.color,
        is_day_off=first.is_day_off,
        sort_order=first.sort_order,
        crosses_midnight=bool(first.start_clock and first.end_clock and first.end_clock < first.start_clock),
        clock_problem=clock_rules.problem(first.start_clock, first.end_clock),
        branches=[ShiftCodeGroupBranchOut(id=outlet.id, name=outlet.name) for outlet in group.branches],
        assignments=group.assignments,
    )
