"""What the branch service receives from the routes."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class BranchDraft:
    name: str
    code: str | None
    receipt_number: str | None
    google_review_url: str | None
    google_location_id: str | None
    latitude: float | None
    longitude: float | None
    attendance_radius_meters: int | None
    cash_float: Decimal | None
    spending_float: Decimal | None
    period_start: date | None
    period_end: date | None


@dataclass(frozen=True)
class BranchChanges:
    """Only the fields that were sent, keyed by attribute name."""

    values: dict
