"""Turns the kitchen report into its response schema."""
from app.core.sorting import RowSorting
from web.management.reports.menu.kitchen.domain import Kitchen, KitchenHour, KitchenOrder
from web.management.reports.menu.kitchen.schemas import KitchenHourOut, KitchenOrderOut, KitchenOut


HOUR_SORTING: RowSorting[KitchenHour] = RowSorting(
    keys={
        "hour": lambda row: row.hour,
        "count": lambda row: row.count,
        "average": lambda row: row.average_minutes,
        "late": lambda row: row.late,
    },
    identity=lambda row: f"{row.hour:02d}",
)

ORDER_SORTING: RowSorting[KitchenOrder] = RowSorting(
    keys={
        "order": lambda row: row.customer_name,
        "items": lambda row: row.items_summary,
        "created_at": lambda row: row.created_at,
        "served_at": lambda row: row.served_at,
        "minutes": lambda row: row.minutes,
    },
    identity=lambda row: row.order_id,
)


def kitchen_out(report: Kitchen, hour_sort: str | None, order_sort: str | None) -> KitchenOut:
    fields = {name: value for name, value in vars(report).items() if name not in ("by_hour", "slowest")}
    busiest = min(report.by_hour, key=lambda row: (-row.count, row.hour), default=None)
    return KitchenOut(
        **fields,
        by_hour=[KitchenHourOut(**vars(hour)) for hour in HOUR_SORTING.apply(report.by_hour, hour_sort)],
        busiest_hour=KitchenHourOut(**vars(busiest)) if busiest else None,
        slowest=[KitchenOrderOut(**vars(order)) for order in ORDER_SORTING.apply(report.slowest, order_sort)],
    )
