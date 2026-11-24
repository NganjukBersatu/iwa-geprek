from decimal import Decimal

STATUS_OUT = "habis"
STATUS_LOW = "menipis"
STATUS_SAFE = "aman"
# Sorting by status goes by urgency, not by the text of the code.
STATUS_ORDER = (STATUS_OUT, STATUS_LOW, STATUS_SAFE)

COST_PLACES = Decimal("1")
DEFAULT_COUNT_NOTE = "Stok opname"
MAX_NOTE_LENGTH = 255
NOT_FOUND = 404
