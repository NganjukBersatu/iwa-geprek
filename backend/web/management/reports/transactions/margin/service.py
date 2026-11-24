"""Builds the margin report."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import orders_in
from app.core.money import decimal_of
from app.models.order import Order
from web.management.reports.common import TENTH, from_today
from web.management.reports.menu.sold_orders import orders_without_lines
from web.management.reports.transactions.margin import repository
from web.management.reports.transactions.margin.domain import MarginReport, MenuMargin


def margin(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> MarginReport:
    """Cost comes from the unit cost snapshotted at checkout, so past margins never move with today's prices."""
    start, end = from_today(start, end)
    window = orders_in(start, end, outlet_id)
    rows = repository.margin_rows(db, window)
    empty_orders, empty_revenue = orders_without_lines(db, (*window, Order.voided_at.is_(None)))
    items: list[MenuMargin] = []
    total_revenue = total_cost = Decimal("0")
    without_cost = 0
    for menu_item_id, name, qty, revenue, cost, lines, costed_lines in rows:
        revenue = decimal_of(revenue)
        total_revenue += revenue
        if not costed_lines:
            without_cost += 1
            items.append(MenuMargin(
                menu_item_id=menu_item_id,
                menu_item_name=name,
                qty=int(qty or 0),
                revenue=revenue,
                cost=None,
                margin=None,
                margin_percent=None,
                cost_complete=False,
            ))
            continue
        cost = decimal_of(cost)
        total_cost += cost
        profit = revenue - cost
        items.append(MenuMargin(
            menu_item_id=menu_item_id,
            menu_item_name=name,
            qty=int(qty or 0),
            revenue=revenue,
            cost=cost,
            margin=profit,
            margin_percent=(profit / revenue * 100).quantize(TENTH) if revenue else None,
            cost_complete=costed_lines == lines,
        ))
    return MarginReport(
        start=start,
        end=end,
        items=items,
        total_revenue=total_revenue,
        total_cost=total_cost,
        total_margin=total_revenue - total_cost,
        menus_without_cost=without_cost,
        orders_without_lines=empty_orders,
        revenue_without_lines=empty_revenue,
    )
