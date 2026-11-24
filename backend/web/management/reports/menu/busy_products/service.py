"""Builds the busy-products report from the sold lines of each product."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import ZERO, decimal_of
from web.management.reports.common import CENT, last_days, percent
from web.management.reports.menu.busy_focus import effective_unit
from web.management.reports.menu.busy_products import repository
from web.management.reports.menu.busy_products.constants import SORT_REVENUE, SORT_TIME
from web.management.reports.menu.busy_products.domain import BusyProductRow, BusyProducts, ProductSeries
from web.management.reports.menu.constants import METRIC_PRODUCTS, METRIC_SALES, PATTERN_DEFAULT_DAYS, UNIT_MINUTE
from web.management.reports.menu.highlights import NONE_YET, highlight
from web.management.reports.menu.sold_orders import count_orders_with_lines, orders_without_lines
from web.management.reports.menu.time_slots import slot_key, slots


def _sorted_rows(rows: list[BusyProductRow], sort: str, position: dict[str, int]) -> None:
    if sort == SORT_REVENUE:
        rows.sort(key=lambda row: (-row.revenue, row.menu_item_name))
    elif sort == SORT_TIME:
        rows.sort(key=lambda row: (position[row.key], -row.qty))
    else:
        rows.sort(key=lambda row: (-row.qty, row.menu_item_name))


@dataclass
class _Tally:
    cells: dict[tuple[str, int], dict] = field(default_factory=dict)
    per_product: dict[str, dict] = field(default_factory=dict)
    slot_qty: list[int] = field(default_factory=list)
    slot_revenue: list[Decimal] = field(default_factory=list)


def _tally(lines: list, unit: str, position: dict[str, int], size: int) -> _Tally:
    """Sums the grouped sold lines per product, per product and slot, and per slot; an order sits in one moment, so its counts never overlap."""
    tally = _Tally(slot_qty=[0] * size, slot_revenue=[ZERO] * size)
    for name, moment, qty, subtotal, orders in lines:
        index = position[slot_key(moment, unit)]
        quantity = int(qty or 0)
        revenue = decimal_of(subtotal)

        cell = tally.cells.setdefault((name, index), {"qty": 0, "revenue": ZERO, "orders": 0})
        cell["qty"] += quantity
        cell["revenue"] += revenue
        cell["orders"] += orders

        product = tally.per_product.setdefault(name, {"qty": 0, "revenue": ZERO, "values": [0] * size})
        product["qty"] += quantity
        product["revenue"] += revenue
        product["values"][index] += quantity

        tally.slot_qty[index] += quantity
        tally.slot_revenue[index] += revenue
    return tally


def busy_products(
    db: Session,
    start: date | None,
    end: date | None,
    unit: str,
    hour: int | None,
    search: str | None,
    sort: str,
    series: int,
    page: int,
    per_page: int,
    outlet_id: str | None,
) -> BusyProducts:
    """Each product per slot; the summary and every percentage cover the whole range, the search only narrows the breakdown."""
    start, end = last_days(start, end, PATTERN_DEFAULT_DAYS)
    unit = effective_unit(unit, hour)
    conditions = valid_orders_in(start, end, outlet_id)

    axis = slots(start, end, unit, hour=hour)
    position = {slot.key: index for index, slot in enumerate(axis)}
    size = len(axis)

    total_transactions = count_orders_with_lines(db, conditions)
    empty_orders, empty_revenue = orders_without_lines(db, conditions)
    all_qty, all_revenue = repository.line_totals(db, conditions)
    total_qty = int(all_qty or 0)
    total_revenue = decimal_of(all_revenue)

    with_minute = unit == UNIT_MINUTE
    whole = _tally(repository.product_lines(db, conditions, None, hour, with_minute), unit, position, size)
    found = _tally(repository.product_lines(db, conditions, search, hour, with_minute), unit, position, size) if search and search.strip() else whole
    cells, per_product = found.cells, found.per_product
    slot_qty, slot_revenue = whole.slot_qty, whole.slot_revenue

    product_key = "revenue" if sort == SORT_REVENUE else "qty"
    ranked = sorted(per_product.items(), key=lambda item: item[1][product_key], reverse=True)
    ranked_whole = sorted(whole.per_product.items(), key=lambda item: item[1][product_key], reverse=True)

    rows = [
        BusyProductRow(
            menu_item_name=name,
            key=axis[index].key,
            label=axis[index].label,
            qty=cell["qty"],
            qty_percent=percent(Decimal(cell["qty"]), Decimal(total_qty)),
            transactions=cell["orders"],
            transactions_percent=percent(Decimal(cell["orders"]), Decimal(total_transactions)),
            revenue=cell["revenue"].quantize(CENT),
            revenue_percent=percent(cell["revenue"], total_revenue),
        )
        for (name, index), cell in cells.items()
    ]
    _sorted_rows(rows, sort, position)

    first = (page - 1) * per_page
    top = ranked_whole[0] if ranked_whole else None

    return BusyProducts(
        start=start,
        end=end,
        unit=unit,
        focus_hour=hour,
        days=(end - start).days + 1,
        slots=axis,
        series=[
            ProductSeries(
                menu_item_name=name,
                total_qty=product["qty"],
                total_revenue=product["revenue"].quantize(CENT),
                values=product["values"],
            )
            for name, product in ranked[:series]
        ],
        total_qty=total_qty,
        total_revenue=total_revenue.quantize(CENT),
        total_transactions=total_transactions,
        orders_without_lines=empty_orders,
        revenue_without_lines=empty_revenue.quantize(CENT),
        product_count=len(whole.per_product),
        top_product=top[0] if top else None,
        top_product_percent=percent(top[1]["revenue"], total_revenue) if top else NONE_YET,
        highlights=[
            highlight(METRIC_SALES, axis, slot_revenue, total_revenue),
            highlight(METRIC_PRODUCTS, axis, [Decimal(value) for value in slot_qty], Decimal(total_qty)),
        ],
        rows=rows[first:first + per_page],
        total_rows=len(rows),
        page=page,
        per_page=per_page,
    )
