from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from web.management.printers.schemas import StationRouteOut
from web.management.branches.constants import (
    MAX_CODE_LENGTH,
    MAX_LOCATION_ID_LENGTH,
    MAX_NAME_LENGTH,
    MAX_NUMBER_LENGTH,
    MAX_RADIUS_METERS,
    MAX_URL_LENGTH,
    MIN_RADIUS_METERS,
)


class BranchCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    code: str | None = Field(None, max_length=MAX_CODE_LENGTH, description="Short code for receipt numbers and reports, such as NGJ")
    receipt_number: str | None = Field(None, max_length=MAX_NUMBER_LENGTH, description="Branch number on the receipt, apart from the code")
    google_review_url: str | None = Field(None, max_length=MAX_URL_LENGTH)
    google_location_id: str | None = Field(None, max_length=MAX_LOCATION_ID_LENGTH)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    attendance_radius_meters: int | None = Field(None, ge=MIN_RADIUS_METERS, le=MAX_RADIUS_METERS)
    period_start: date | None = Field(None, description="First day of the running closing period; the following months repeat its day")
    period_end: date | None = Field(None, description="Last day of the running closing period; sent together with period_start")
    cash_float: Decimal | None = Field(None, ge=0, description="Cash that must be back in the drawer when a shift closes")
    spending_float: Decimal | None = Field(None, ge=0, description="When set, closing a shift has three parts: float, spending, revenue")


class BranchUpdateIn(BaseModel):
    """A field left out stays as it was; a text sent empty is cleared, except the name."""

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    code: str | None = Field(None, max_length=MAX_CODE_LENGTH)
    receipt_number: str | None = Field(None, max_length=MAX_NUMBER_LENGTH)
    is_active: bool | None = Field(None, description="A closed branch is deactivated, not deleted, so its reports stay readable")
    google_review_url: str | None = Field(None, max_length=MAX_URL_LENGTH)
    google_location_id: str | None = Field(None, max_length=MAX_LOCATION_ID_LENGTH)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    attendance_radius_meters: int | None = Field(None, ge=MIN_RADIUS_METERS, le=MAX_RADIUS_METERS)
    period_start: date | None = Field(None, description="New running period and pattern from here on; earlier periods keep their dates")
    period_end: date | None = None
    cash_float: Decimal | None = Field(None, ge=0)
    spending_float: Decimal | None = Field(None, ge=0)


class BranchOut(BaseModel):
    id: str
    name: str
    code: str | None
    receipt_number: str | None
    is_active: bool
    latitude: float | None
    longitude: float | None
    attendance_radius_meters: int
    google_review_url: str | None
    google_location_id: str | None
    cash_float: Decimal | None
    spending_float: Decimal | None
    created_at: datetime
    removal_started_at: datetime | None = Field(None, description="Set while a permanent removal is under way; the branch can no longer be reopened")


class BranchRemovalIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH, description="The branch name typed by the admin to confirm")


class BranchRemovalOut(BaseModel):
    """One step of a permanent removal; the screen calls again until done."""

    done: bool
    finished_parts: int
    total_parts: int


class BranchPeriodIn(BaseModel):
    start: date
    end: date


class BranchReadinessOut(BaseModel):
    """Yang masih kurang sebelum cabang siap jualan; dihitung dari data yang sama dengan tablet."""

    settings_ready: bool
    location_ready: bool
    # Tablet terdaftar yang memegang stasiun Kasir; kosong berarti belum ada yang bisa bertransaksi.
    cashier_name: str | None
    stations: list[StationRouteOut]
