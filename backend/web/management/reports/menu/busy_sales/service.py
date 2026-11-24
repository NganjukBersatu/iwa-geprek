"""Builds the busy-sales report from sold orders and their lines."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import ZERO, decimal_of
from web.management.reports.common import CENT, divide, last_days, percent
from web.management.reports.menu.busy_focus import effective_unit
from web.management.reports.menu.busy_sales import repository
from web.management.reports.menu.busy_sales.domain import BusySales, BusySalesRow
from web.management.reports.menu.constants import METRIC_SALES, METRIC_TRANSACTIONS, PATTERN_DEFAULT_DAYS, UNIT_MINUTE
from web.management.reports.menu.highlights import highlight
from web.management.reports.menu.time_slots import slot_key, slots


def busy_sales(
    db: Session, start: date | None, end: date | None, unit: str, hour: int | None, outlet_id: str | None
) -> BusySales:
    """The whole shop per slot, with no product dimension; repeating slots also carry their averages."""
    start, end = last_days(start, end, PATTERN_DEFAULT_DAYS)
    unit = effective_unit(unit, hour)
    conditions = valid_orders_in(start, end, outlet_id)

    axis = slots(start, end, unit, hour=hour)
    position = {slot.key: index for index, slot in enumerate(axis)}
    size = len(axis)
    transactions = [0] * size
    quantities = [0] * size
    sales = [ZERO] * size
    customers_per_slot: list[set] = [set() for _ in range(size)]
    customers: set = set()
    without_customer = 0

    with_minute = unit == UNIT_MINUTE
    for moment, customer_id, orders, total in repository.order_sales(db, conditions, hour, with_minute):
        index = position[slot_key(moment, unit)]
        transactions[index] += orders
        sales[index] += decimal_of(total)
        if customer_id:
            customers_per_slot[index].add(customer_id)
            customers.add(customer_id)
        else:
            without_customer += orders

    for moment, qty in repository.line_quantities(db, conditions, hour, with_minute):
        quantities[position[slot_key(moment, unit)]] += int(qty or 0)

    total_transactions = sum(transactions)
    total_quantity = sum(quantities)
    total_sales = sum(sales, ZERO)

    rows = [
        BusySalesRow(
            slot=slot,
            transactions=transactions[index],
            products=quantities[index],
            customers=len(customers_per_slot[index]),
            sales=sales[index].quantize(CENT),
            transactions_percent=percent(Decimal(transactions[index]), Decimal(total_transactions)),
            products_percent=percent(Decimal(quantities[index]), Decimal(total_quantity)),
            sales_percent=percent(sales[index], total_sales),
            transactions_average=divide(Decimal(transactions[index]), slot.occurrences),
            products_average=divide(Decimal(quantities[index]), slot.occurrences),
            customers_average=divide(Decimal(len(customers_per_slot[index])), slot.occurrences),
            sales_average=divide(sales[index], slot.occurrences),
        )
        for index, slot in enumerate(axis)
    ]

    return BusySales(
        start=start,
        end=end,
        unit=unit,
        focus_hour=hour,
        days=(end - start).days + 1,
        total_sales=total_sales.quantize(CENT),
        total_transactions=total_transactions,
        total_products=total_quantity,
        total_customers=len(customers),
        average_per_transaction=divide(total_sales, total_transactions),
        transactions_without_customer=without_customer,
        highlights=[
            highlight(METRIC_SALES, axis, sales, total_sales),
            highlight(METRIC_TRANSACTIONS, axis, [Decimal(value) for value in transactions], Decimal(total_transactions)),
        ],
        rows=rows,
    )
