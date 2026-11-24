"""Turns category entries into response schemas."""
from web.management.shift_categories.domain import CategoryEntry
from web.management.shift_categories.schemas import ShiftCategoryOut


def category_out(entry: CategoryEntry) -> ShiftCategoryOut:
    category = entry.category
    return ShiftCategoryOut(
        id=category.id,
        name=category.name,
        shift_kind=category.shift_kind,
        start_from=category.shift_start_from,
        start_until=category.shift_start_until,
        codes=entry.codes,
        mismatched=entry.mismatched,
    )
