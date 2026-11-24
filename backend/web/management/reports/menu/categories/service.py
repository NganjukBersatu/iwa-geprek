"""Builds the categories report: sales and profit per menu category against the period before, per menu for drilling in, and the menu items that did not sell at all."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import ZERO, decimal_of
from app.core.pricing import price_map
from web.management.reports.common import month_to_date, optional_percent
from web.management.reports.menu import messages
from web.management.reports.menu.categories import repository
from web.management.reports.menu.categories.domain import Categories, CategorySales, MenuSales, UnsoldMenu
from web.management.reports.menu.sold_orders import orders_without_lines
from web.management.reports.sales.comparison.domain import ComparisonMode
from web.management.reports.sales.comparison.previous_range import previous_range


def _name_of(category: str | None, menu_id: str | None) -> str:
    return category or (messages.NO_CATEGORY if menu_id else messages.DELETED_MENU)


def _profit(revenue, cost, costed_lines: int):
    """Laba dari baris yang modalnya tercatat; None bila tidak ada satu pun, karena nol berarti lain."""
    return decimal_of(revenue) - decimal_of(cost) if costed_lines > 0 else None


def _change(now, before):
    previous = decimal_of(before)
    return optional_percent(decimal_of(now) - previous, previous)


def categories(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> Categories:
    start, end = month_to_date(start, end)
    conditions = valid_orders_in(start, end, outlet_id)
    previous_start, previous_end, _label = previous_range(start, end, ComparisonMode.AUTO, None, None)

    per_category: dict[str, dict] = {}
    menus: list[MenuSales] = []
    sold: set[str] = set()
    total_revenue = ZERO
    for category, menu_id, menu_name, qty, revenue, cost, lines, costed in repository.sales_by_category_and_menu(db, conditions):
        if menu_id:
            sold.add(menu_id)
        name = _name_of(category, menu_id)
        lines, costed = int(lines or 0), int(costed or 0)
        tally = per_category.setdefault(name, {"qty": 0, "revenue": ZERO, "cost": ZERO, "lines": 0, "costed": 0, "menus": set()})
        tally["qty"] += int(qty or 0)
        tally["revenue"] += decimal_of(revenue)
        tally["cost"] += decimal_of(cost)
        tally["lines"] += lines
        tally["costed"] += costed
        if menu_id:
            tally["menus"].add(menu_id)
        total_revenue += decimal_of(revenue)
        menus.append(
            MenuSales(
                menu_item_id=menu_id,
                name=menu_name or messages.DELETED_MENU,
                category=name,
                qty=int(qty or 0),
                revenue=decimal_of(revenue),
                profit=_profit(revenue, cost, costed),
                cost_complete=costed == lines,
            )
        )

    previous: dict[str, object] = {}
    for category, deleted, value in repository.revenue_by_category(db, valid_orders_in(previous_start, previous_end, outlet_id)):
        name = _name_of(category, None if deleted else "known")
        previous[name] = previous.get(name, ZERO) + decimal_of(value)
    category_sales = sorted(
        (
            CategorySales(
                category=name,
                qty=tally["qty"],
                revenue=tally["revenue"],
                menu_count=len(tally["menus"]),
                revenue_percent=optional_percent(tally["revenue"], total_revenue) or ZERO,
                profit=_profit(tally["revenue"], tally["cost"], tally["costed"]),
                cost_complete=tally["costed"] == tally["lines"],
                previous_revenue=previous.get(name, ZERO),
                revenue_change_percent=_change(tally["revenue"], previous.get(name, ZERO)),
            )
            for name, tally in per_category.items()
        ),
        key=lambda sales: sales.revenue,
        reverse=True,
    )

    catalogue = repository.menus_with_category(db)
    unsold = [(menu, category) for menu, category in catalogue if menu.id not in sold]
    prices = price_map(db, outlet_id, [menu for menu, _ in unsold])
    last_sold = repository.last_sold(db, [menu.id for menu, _ in unsold], outlet_id)

    empty_orders, empty_revenue = orders_without_lines(db, conditions)

    return Categories(
        start=start,
        end=end,
        previous_start=previous_start,
        previous_end=previous_end,
        total_revenue=total_revenue,
        previous_total_revenue=sum(previous.values(), ZERO),
        orders_without_lines=empty_orders,
        revenue_without_lines=empty_revenue,
        categories=category_sales,
        menus=sorted(menus, key=lambda row: row.revenue, reverse=True),
        total_menu_count=len(catalogue),
        sold_menu_count=len(sold),
        unsold=[
            UnsoldMenu(
                menu_item_id=menu.id,
                name=menu.name,
                category=category,
                price=prices[menu.id],
                is_available=menu.is_available,
                last_sold_at=last_sold.get(menu.id),
                created_at=menu.created_at,
            )
            for menu, category in unsold
        ],
    )
