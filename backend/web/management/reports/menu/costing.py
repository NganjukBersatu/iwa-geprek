"""Known cost of a grouped option row in the variant and extra reports."""
from decimal import Decimal


def known_cost(row) -> Decimal | None:
    """None when no line of the row has a known cost, which is not the same as zero."""
    return Decimal(str(row.cost)) if int(row.costed_lines) > 0 else None
