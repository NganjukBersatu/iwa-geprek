"""Month arithmetic shared by the trend bars and the comparison period."""
import calendar
from datetime import date

from web.management.reports.sales.constants import MONTHS_PER_YEAR


def month_end(day: date) -> date:
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


def months_back(day: date, months: int) -> date:
    """The first of the month `months` before the month of `day`, counted in absolute months."""
    absolute = day.year * MONTHS_PER_YEAR + (day.month - 1) - months
    return date(absolute // MONTHS_PER_YEAR, absolute % MONTHS_PER_YEAR + 1, 1)


def same_day_months_back(day: date, months: int) -> date:
    """The same day `months` earlier, clamped to the end of that month (31 Mar becomes 28/29 Feb)."""
    year, month = day.year, day.month - months
    while month <= 0:
        month += MONTHS_PER_YEAR
        year -= 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))
