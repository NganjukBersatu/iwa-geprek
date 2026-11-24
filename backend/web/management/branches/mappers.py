"""Turns branches into response schemas."""
from app.core.sorting import RowSorting
from app.models.outlet import Outlet
from web.management.branches.constants import DEFAULT_RADIUS_METERS
from web.management.branches.schemas import BranchOut


SORTING: RowSorting[BranchOut] = RowSorting(
    keys={
        "name": lambda row: row.name,
        # A branch without an attendance point comes first ascending, so the ones still to set up are easy to find.
        "location": lambda row: row.latitude is not None and row.longitude is not None,
        "radius": lambda row: row.attendance_radius_meters,
        "cash_float": lambda row: row.cash_float,
        "status": lambda row: row.is_active,
    },
    identity=lambda row: row.id,
)


def branch_out(outlet: Outlet) -> BranchOut:
    return BranchOut(
        id=outlet.id,
        name=outlet.name,
        code=outlet.code,
        receipt_number=outlet.receipt_number,
        is_active=bool(outlet.is_active),
        latitude=outlet.latitude,
        longitude=outlet.longitude,
        attendance_radius_meters=outlet.attendance_radius_meters or DEFAULT_RADIUS_METERS,
        google_review_url=outlet.google_review_url,
        google_location_id=outlet.google_location_id,
        cash_float=outlet.cash_float,
        spending_float=outlet.spending_float,
        created_at=outlet.created_at,
        removal_started_at=outlet.removal_started_at,
    )
