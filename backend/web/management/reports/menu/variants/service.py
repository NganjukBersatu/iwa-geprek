"""Builds the variants report from the sold lines that carry a variant."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in

from web.management.reports.common import last_days, percent_tenth
from web.management.reports.menu import messages
from web.management.reports.menu.constants import PATTERN_DEFAULT_DAYS
from web.management.reports.menu.costing import known_cost
from web.management.reports.menu.variants import repository
from web.management.reports.menu.variants.domain import VariantRow, Variants


def variants(db: Session, start: date | None, end: date | None, by_menu: bool, outlet_id: str | None) -> Variants:
    """Variants do not change the price, so they compare by portions and by the revenue of the lines using them."""
    start, end = last_days(start, end, PATTERN_DEFAULT_DAYS)
    rows = repository.variant_sales(db, valid_orders_in(start, end, outlet_id), by_menu)

    group_portions: dict[str, int] = {}
    for row in rows:
        group = row.group_name or ""
        group_portions[group] = group_portions.get(group, 0) + int(row.portions)

    result: list[VariantRow] = []
    for row in rows:
        group = row.group_name or ""
        cost = known_cost(row)
        result.append(
            VariantRow(
                group=group or messages.NO_GROUP,
                option=row.option_name,
                menu=row.menu_item_name if by_menu else None,
                portions=int(row.portions),
                transactions=int(row.transactions),
                revenue=Decimal(str(row.revenue)),
                portions_percent=percent_tenth(Decimal(int(row.portions)), Decimal(group_portions[group])),
                cost=cost,
                margin=(Decimal(str(row.costed_revenue)) - cost) if cost is not None else None,
            )
        )
    result.sort(key=lambda variant: (variant.group.lower(), -variant.portions, variant.option.lower(), variant.menu or ""))
    return Variants(start=start, end=end, by_menu=by_menu, rows=result)
