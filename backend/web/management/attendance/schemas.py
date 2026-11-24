from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.attendance import AttendanceStatus
from web.management.attendance.constants import MAX_NOTE_LENGTH


class MarkIn(BaseModel):
    user_id: str
    date: date
    shift_code_id: str | None = None
    status: AttendanceStatus
    schedule_id: str | None = None
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    clock_in_at: datetime | None = Field(None, description="Only for a manual correction; marking present fills it from the server clock")
    clock_out_at: datetime | None = None


class EditIn(BaseModel):
    """A field left out stays as it was; a clock or note sent as null is cleared."""

    status: AttendanceStatus | None = None
    clock_in_at: datetime | None = None
    clock_out_at: datetime | None = None
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)


class ProofOut(BaseModel):
    """Where and how one clock event was made; every field is empty for a record that was marked by an admin."""

    photo_url: str | None
    latitude: float | None
    longitude: float | None
    accuracy_meters: float | None
    mode: str | None
    note: str | None
    distance_meters: float | None
    radius_meters: int | None
    # Kapan server menerima absen ini; kosong untuk absen yang dicatat admin atau dikirim tanpa kunci.
    submitted_at: datetime | None
    submitted_late: bool
    needs_review: bool


class BranchPointOut(BaseModel):
    """The cafe of the branch, drawn on the map next to where the clock event was made."""

    latitude: float
    longitude: float


class AttendanceOut(BaseModel):
    id: str
    user_id: str
    username: str
    name: str | None
    role_name: str | None
    date: date
    shift_code: str | None
    shift_code_color: str | None
    status: AttendanceStatus
    clock_in_at: datetime | None
    clock_out_at: datetime | None
    auto_closed: bool
    schedule_id: str | None
    note: str | None
    outside_schedule_reason: str | None
    clock_in: ProofOut
    clock_out: ProofOut
    branch_location: BranchPointOut | None
    late_minutes: int
    penalty: int
    work_minutes: int | None
    created_at: datetime
    updated_at: datetime


class AttendancePageOut(BaseModel):
    items: list[AttendanceOut]
    total: int
    page: int
    size: int
