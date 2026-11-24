"""Builds the extras report from the extras attached to sold lines."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import ZERO, decimal_of
from web.management.reports.common import last_days, percent_tenth
from web.management.reports.menu.constants import PATTERN_DEFAULT_DAYS
from web.management.reports.menu.costing import known_cost
from web.management.reports.menu.extras import repository
from web.management.reports.menu.extras.domain import ExtraRow, Extras


def extras(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> Extras:
    """Quantity is the amount per portion times the portions; revenue uses the price at the time of sale."""
    start, end = last_days(start, end, PATTERN_DEFAULT_DAYS)
    conditions = valid_orders_in(start, end, outlet_id)
    rows = repository.extra_sales(db, conditions)

    total_extra = sum((Decimal(str(row.revenue)) for row in rows), ZERO)
    total_revenue = decimal_of(repository.line_revenue(db, conditions))
    result: list[ExtraRow] = []
    for row in rows:
        cost = known_cost(row)
        revenue = Decimal(str(row.revenue))
        result.append(
            ExtraRow(
                extra=row.extra_name,
                quantity=int(row.quantity),
                transactions=int(row.transactions),
                revenue=revenue,
                revenue_percent=percent_tenth(revenue, total_extra),
                cost=cost,
                profit=(Decimal(str(row.costed_revenue)) - cost) if cost is not None else None,
            )
        )
    result.sort(key=lambda extra: (-extra.quantity, extra.extra.lower()))
    return Extras(
        start=start,
        end=end,
        total_extra_revenue=total_extra,
        total_quantity=sum(extra.quantity for extra in result),
        total_revenue=total_revenue,
        revenue_percent=percent_tenth(total_extra, total_revenue),
        rows=result,
    )
