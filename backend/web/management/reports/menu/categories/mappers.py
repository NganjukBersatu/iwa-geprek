"""Turns the categories report into its response schema."""
from app.core.sorting import RowSorting
from web.management.reports.menu.categories.domain import Categories, CategorySales, MenuSales, UnsoldMenu
from web.management.reports.menu.categories.schemas import CategoriesOut, CategorySalesOut, MenuSalesOut, UnsoldMenuOut


CATEGORY_SORTING: RowSorting[CategorySales] = RowSorting(
    keys={
        "category": lambda row: row.category,
        "qty": lambda row: row.qty,
        "revenue": lambda row: row.revenue,
        "profit": lambda row: row.profit,
        "change": lambda row: row.revenue_change_percent,
    },
    identity=lambda row: row.category,
)

MENU_SORTING: RowSorting[MenuSales] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "qty": lambda row: row.qty,
        "revenue": lambda row: row.revenue,
        "profit": lambda row: row.profit,
    },
    identity=lambda row: (row.category, row.menu_item_id or row.name),
)

UNSOLD_SORTING: RowSorting[UnsoldMenu] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "category": lambda row: row.category,
        "price": lambda row: row.price,
        "last_sold": lambda row: row.last_sold_at,
        "created": lambda row: row.created_at,
    },
    identity=lambda row: row.menu_item_id,
)


def categories_out(report: Categories, sort: str | None, unsold_sort: str | None, menu_sort: str | None) -> CategoriesOut:
    fields = {name: value for name, value in vars(report).items() if name not in ("categories", "menus", "unsold")}
    return CategoriesOut(
        **fields,
        categories=[CategorySalesOut(**vars(sales)) for sales in CATEGORY_SORTING.apply(report.categories, sort)],
        menus=[MenuSalesOut(**vars(menu)) for menu in MENU_SORTING.apply(report.menus, menu_sort)],
        unsold=[UnsoldMenuOut(**vars(menu)) for menu in UNSOLD_SORTING.apply(report.unsold, unsold_sort)],
    )
