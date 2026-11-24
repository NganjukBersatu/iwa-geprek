"""Turns menu categories into their response schema."""
from app.core.sorting import RowSorting
from web.management.menu_categories.repository import Row
from web.management.menu_categories.schemas import MenuCategoryRecordOut

SORTING: RowSorting[MenuCategoryRecordOut] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "menus": lambda row: row.menu_count,
        "station": lambda row: row.station_name,
    },
    identity=lambda row: row.id,
)


def category_out(row: Row) -> MenuCategoryRecordOut:
    category, menu_count, station_name = row
    return MenuCategoryRecordOut(id=category.id, name=category.name, menu_count=menu_count, station_name=station_name)
