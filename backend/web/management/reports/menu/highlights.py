"""Busiest and quietest slot of a metric in the busiest-times reports, from calculation to response."""
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel

from web.management.reports.common import CENT, divide, percent
from web.management.reports.menu.time_slots import TimeSlot

NONE_YET = Decimal("0.00")


@dataclass(frozen=True)
class Highlight:
    """Busiest and quietest slot of one metric, chosen by the average per occurrence like the chart draws it."""

    metric: str
    peak_label: str | None
    peak_value: Decimal
    peak_percent: Decimal
    quiet_label: str | None
    quiet_value: Decimal
    ratio: Decimal | None


class HighlightOut(BaseModel):
    metric: str
    peak_label: str | None
    peak_value: Decimal
    peak_percent: Decimal
    quiet_label: str | None
    quiet_value: Decimal
    ratio: Decimal | None


def highlight(metric: str, axis: list[TimeSlot], values: list[Decimal], total: Decimal) -> Highlight:
    """The peak uses the average per occurrence like the chart; its percent uses the raw sum against the whole range."""
    if not axis:
        return Highlight(metric, None, NONE_YET, NONE_YET, None, NONE_YET, None)
    averages = [divide(values[index], slot.occurrences) for index, slot in enumerate(axis)]
    top = max(range(len(axis)), key=lambda index: averages[index])
    low = min(range(len(axis)), key=lambda index: averages[index])
    ratio = (averages[top] / averages[low]).quantize(CENT) if averages[low] > 0 else None
    return Highlight(
        metric=metric,
        peak_label=axis[top].label,
        peak_value=averages[top],
        peak_percent=percent(values[top], total),
        quiet_label=axis[low].label,
        quiet_value=averages[low],
        ratio=ratio,
    )


def highlight_out(item: Highlight) -> HighlightOut:
    return HighlightOut(**vars(item))
