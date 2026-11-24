"""Sort keys and limits of the busy-products report, kept identical to the legacy routes."""

SORT_QTY = "qty"
SORT_REVENUE = "revenue"
SORT_TIME = "time"
SORT_PATTERN = f"^({SORT_QTY}|{SORT_REVENUE}|{SORT_TIME})$"

SEARCH_MAX_LENGTH = 80
SERIES_DEFAULT = 5
SERIES_MAX = 8
PRODUCTS_PER_PAGE_DEFAULT = 25
PRODUCTS_PER_PAGE_MIN = 5
PRODUCTS_PER_PAGE_MAX = 200
