"""Units, metrics, and defaults shared by the menu reports, kept identical to the legacy routes."""

UNIT_HOUR = "hour"
UNIT_WEEKDAY = "weekday"
UNIT_DATE = "date"
UNIT_MONTH = "month"
# The minute unit is never requested directly; an hour slot becomes it when the report dives into that hour.
UNIT_MINUTE = "minute"
UNIT_PATTERN = f"^({UNIT_HOUR}|{UNIT_WEEKDAY}|{UNIT_DATE}|{UNIT_MONTH})$"

METRIC_SALES = "sales"
METRIC_TRANSACTIONS = "transactions"
METRIC_PRODUCTS = "products"

# Busy-time and option reports look for patterns, so they default to the last 30 days rather than this month.
PATTERN_DEFAULT_DAYS = 30

LAST_HOUR = 23
HOUR_DESCRIPTION = "Fill to see the minutes of that hour; only with unit 'hour'"
