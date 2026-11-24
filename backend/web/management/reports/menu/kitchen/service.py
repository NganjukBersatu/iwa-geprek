"""Builds the kitchen report from the time between order creation and serving."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in

from web.management.reports.common import TENTH, month_to_date, optional_percent
from web.management.reports.menu import item_summary
from web.management.reports.menu.kitchen import repository
from web.management.reports.menu.kitchen.constants import KITCHEN_SLOWEST_LIMIT
from web.management.reports.menu.kitchen.domain import Kitchen, KitchenHour, KitchenOrder

SECONDS_PER_MINUTE = 60
HALF = 2


def _rounded_minutes(seconds: float) -> Decimal:
    return Decimal(str(max(0.0, seconds / SECONDS_PER_MINUTE))).quantize(TENTH)


def _bucket_minutes(whole: int, exact: bool) -> Decimal:
    """The rounded minutes every order of a whole-second bucket has. A time with a fraction sits strictly between two whole seconds,
    and the rounding only turns at multiples of three seconds, so half a second past the bucket stands for all of them."""
    return _rounded_minutes(whole if exact else whole + 0.5)


def _median(counted: dict[Decimal, int]) -> Decimal | None:
    """`counted` maps a rounded minutes value to how many orders have it; an even count averages the two middle values."""
    count = sum(counted.values())
    if not count:
        return None

    def at(position: int) -> Decimal:
        passed = 0
        for value in sorted(counted):
            passed += counted[value]
            if position < passed:
                return value
        raise IndexError(position)

    middle = count // HALF
    if count % HALF:
        return at(middle)
    return ((at(middle - 1) + at(middle)) / HALF).quantize(TENTH)


def _average(counted: dict[Decimal, int]) -> Decimal:
    return (sum((value * number for value, number in counted.items()), Decimal(0)) / sum(counted.values())).quantize(TENTH)


def kitchen(db: Session, start: date | None, end: date | None, threshold: int, outlet_id: str | None) -> Kitchen:
    """Averages cover served orders only; orders still on the board are counted separately."""
    start, end = month_to_date(start, end)
    conditions = valid_orders_in(start, end, outlet_id)
    unserved = repository.count_unserved(db, conditions)

    counted: dict[Decimal, int] = {}
    counted_by_hour: dict[int, dict[Decimal, int]] = {}
    for hour, whole, exact, orders in repository.duration_groups(db, conditions):
        minutes = _bucket_minutes(whole, exact)
        counted[minutes] = counted.get(minutes, 0) + orders
        in_hour = counted_by_hour.setdefault(hour, {})
        in_hour[minutes] = in_hour.get(minutes, 0) + orders

    count = sum(counted.values())
    late = sum(number for minutes, number in counted.items() if minutes > threshold)

    slowest = [
        (_rounded_minutes((served_at - created_at).total_seconds()), order_id, customer_name, table_no, created_at, served_at)
        for order_id, customer_name, table_no, created_at, served_at in repository.slowest_orders(db, conditions, KITCHEN_SLOWEST_LIMIT)
    ]
    slowest.sort(key=lambda duration: duration[0], reverse=True)
    texts = item_summary.summaries(db, [duration[1] for duration in slowest])

    return Kitchen(
        start=start,
        end=end,
        threshold_minutes=threshold,
        served_count=count,
        unserved_count=unserved,
        average_minutes=_average(counted) if count else None,
        median_minutes=_median(counted),
        max_minutes=max(counted) if count else None,
        late=late,
        late_percent=optional_percent(late, count),
        by_hour=[
            KitchenHour(
                hour=hour,
                count=sum(in_hour.values()),
                average_minutes=_average(in_hour),
                late=sum(number for value, number in in_hour.items() if value > threshold),
            )
            for hour, in_hour in sorted(counted_by_hour.items())
        ],
        slowest=[
            KitchenOrder(
                order_id=order_id,
                customer_name=customer_name,
                table_no=table_no,
                created_at=created_at,
                served_at=served_at,
                minutes=minutes,
                items_summary=texts.get(order_id, ""),
            )
            for minutes, order_id, customer_name, table_no, created_at, served_at in slowest
        ],
    )
