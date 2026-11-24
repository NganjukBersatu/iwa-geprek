"""Figures shared by more than one inventory report."""
from decimal import Decimal

QTY = Decimal("0.001")

# The turnover report defaults to this dormant span and the inventory value always uses it, so both name the same count.
DORMANT_DAYS = 30
