"""Builds the visitor breakdown: transactions and revenue per visitor category and gender, and per day.

The unit is the transaction, not the head count: the category and gender are recorded once per order. Orders the
cashier left blank are grouped as unrecorded, so the percentages never pretend every visitor was recorded. Grouping is
by the label copied onto the order, so a category that was renamed or deleted still reads, and branches with their own lists add up.
"""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.money import ZERO, decimal_of, round_rupiah
from web.management.reports.common import month_to_date, percent_tenth
from web.management.reports.sales.visitor_breakdown import repository
from web.management.reports.sales.visitor_breakdown.domain import VisitorBreakdown, VisitorDay, VisitorGroup

UNRECORDED = "Tidak dicatat"


def _groups(tally: dict[str, list], total: int) -> list[VisitorGroup]:
    """Most transactions first, with the unrecorded group always last."""
    ordered = sorted(tally.items(), key=lambda item: (item[0] == UNRECORDED, -item[1][0], item[0]))
    return [VisitorGroup(label=label, transactions=count, revenue=revenue, percent=percent_tenth(Decimal(count), Decimal(total))) for label, (count, revenue) in ordered]


def _add(tally: dict[str, list], label: str, orders: int, revenue: Decimal) -> None:
    entry = tally.setdefault(label, [0, ZERO])
    entry[0] += orders
    entry[1] += revenue


def visitor_breakdown(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> VisitorBreakdown:
    start, end = month_to_date(start, end)
    groups = repository.tallies_between(db, start, end, outlet_id)

    categories: dict[str, list] = {}
    genders: dict[str, list] = {}
    per_day: dict[date, dict] = {}
    with_category = with_gender = 0
    total_revenue = ZERO

    total_orders = 0
    for order_day, category, gender, orders, total in groups:
        revenue = decimal_of(total)
        category = category or UNRECORDED
        gender = gender or UNRECORDED
        total_orders += orders
        with_category += orders if category != UNRECORDED else 0
        with_gender += orders if gender != UNRECORDED else 0
        total_revenue += revenue
        _add(categories, category, orders, revenue)
        _add(genders, gender, orders, revenue)
        day = per_day.setdefault(order_day, {"transactions": 0, "revenue": ZERO, "categories": {}, "genders": {}})
        day["transactions"] += orders
        day["revenue"] += revenue
        day["categories"][category] = day["categories"].get(category, 0) + orders
        day["genders"][gender] = day["genders"].get(gender, 0) + orders

    days = []
    current = start
    while current <= end:
        found = per_day.get(current)
        days.append(
            VisitorDay(
                date=current,
                transactions=found["transactions"] if found else 0,
                revenue=found["revenue"] if found else ZERO,
                average_transaction=round_rupiah(found["revenue"] / found["transactions"]) if found and found["transactions"] else ZERO,
                categories=found["categories"] if found else {},
                genders=found["genders"] if found else {},
            )
        )
        current += timedelta(days=1)

    return VisitorBreakdown(
        start=start,
        end=end,
        total_transactions=total_orders,
        total_revenue=total_revenue,
        with_category=with_category,
        with_gender=with_gender,
        by_category=_groups(categories, total_orders),
        by_gender=_groups(genders, total_orders),
        days=days,
    )
