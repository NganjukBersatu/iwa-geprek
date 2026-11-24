"""Turns the busy-products report into its response schema."""
from web.management.reports.menu.busy_products.domain import BusyProducts
from web.management.reports.menu.busy_products.schemas import BusyProductRowOut, BusyProductsOut, ProductSeriesOut, TimeSlotOut
from web.management.reports.menu.highlights import highlight_out
from web.management.reports.menu.time_slots import TimeSlot


def _slot_out(slot: TimeSlot) -> TimeSlotOut:
    return TimeSlotOut(key=slot.key, label=slot.label, occurrences=slot.occurrences)


def busy_products_out(report: BusyProducts) -> BusyProductsOut:
    nested = ("slots", "series", "highlights", "rows")
    fields = {name: value for name, value in vars(report).items() if name not in nested}
    return BusyProductsOut(
        **fields,
        slots=[_slot_out(slot) for slot in report.slots],
        series=[ProductSeriesOut(**vars(series)) for series in report.series],
        highlights=[highlight_out(item) for item in report.highlights],
        rows=[BusyProductRowOut(**vars(row)) for row in report.rows],
    )
