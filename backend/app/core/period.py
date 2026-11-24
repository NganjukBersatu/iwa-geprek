"""Calendar months, which is how monthly views are asked for."""
import calendar
from datetime import date

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
MONTH_SEPARATOR = "-"
FIRST_DAY = 1


def parse_month(text: str) -> date:
    year, month = text.split(MONTH_SEPARATOR)
    return date(int(year), int(month), FIRST_DAY)


def month_bounds(any_day: date) -> tuple[date, date]:
    last = calendar.monthrange(any_day.year, any_day.month)[1]
    return any_day.replace(day=FIRST_DAY), any_day.replace(day=last)


def month_label(any_day: date) -> str:
    return f"{any_day.year:04d}{MONTH_SEPARATOR}{any_day.month:02d}"
