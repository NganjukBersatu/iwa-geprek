"""HTTP surface of attendance; every rule lives in the service."""
from datetime import datetime

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.auth import current_user, require_permission
from app.core.clock import now
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.core.http import public_base_url
from app.core.uploads import UploadedFile
from app.employee.attendance import clock_events, mappers, messages, repository, service
from app.employee.attendance.constants import (
    LOCATION_INSIDE,
    LOCATION_MODES,
    MAX_ACCURACY_METERS,
    MAX_ID_LENGTH,
    MAX_IDEMPOTENCY_KEY_LENGTH,
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_NOTE_LENGTH,
    MAX_NOTICE_IDS,
    MIN_IDEMPOTENCY_KEY_LENGTH,
    PERMISSION_SELF_ATTENDANCE,
)
from app.employee.attendance.location_validation import Location
from app.employee.attendance.upload import RULE
from app.employee.attendance.schemas import EmployeeAttendanceOut, AttendanceStateOut
from app.models.attendance_clock_event import SOURCE_DEVICE_CLOCK, SOURCE_SERVER_ANCHORED
from app.models.user import User

router = APIRouter(prefix="/attendance", tags=["v2-attendance"])


def _as_http(error: DomainError) -> HTTPException:
    return refusal(error)


async def _clock_input(
    latitude: float = Form(..., ge=-MAX_LATITUDE, le=MAX_LATITUDE),
    longitude: float = Form(..., ge=-MAX_LONGITUDE, le=MAX_LONGITUDE),
    accuracy: float = Form(..., ge=0, le=MAX_ACCURACY_METERS),
    location_mode: str = Form(LOCATION_INSIDE),
    location_note: str | None = Form(None, max_length=MAX_NOTE_LENGTH),
    photo: UploadFile = File(...),
) -> tuple[Location, UploadedFile]:
    if location_mode not in LOCATION_MODES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, messages.INVALID_LOCATION_MODE)
    try:
        checked = await uploads.receive(photo, RULE)
    except DomainError as error:
        raise _as_http(error) from error
    return Location(latitude, longitude, accuracy, location_mode, location_note), checked


def _submission(
    idempotency_key: str | None = Form(None, min_length=MIN_IDEMPOTENCY_KEY_LENGTH, max_length=MAX_IDEMPOTENCY_KEY_LENGTH),
    captured_at: datetime | None = Form(None),
    time_source: str = Form(SOURCE_DEVICE_CLOCK),
) -> clock_events.Submission | None:
    """Absen langsung tidak membawa apa pun; absen dari antrean membawa kunci, dan bila terlambat juga waktu ambilnya."""
    if idempotency_key is None:
        if captured_at is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, messages.CAPTURE_NEEDS_KEY)
        return None
    if captured_at is None:
        return clock_events.Submission(idempotency_key, None, SOURCE_SERVER_ANCHORED)
    if captured_at.tzinfo is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, messages.INVALID_CAPTURE_TIME)
    if time_source not in clock_events.TIME_SOURCES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, messages.INVALID_TIME_SOURCE)
    return clock_events.Submission(idempotency_key, captured_at, time_source)


@router.get("/state", response_model=AttendanceStateOut)
def attendance_state(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    instant = now()
    state = service.get_state(db, user, instant)
    base_url = public_base_url()
    return AttendanceStateOut(
        date=state.day,
        server_time=instant,
        can_clock_in=state.can_clock_in,
        can_clock_out=state.can_clock_out,
        attendance=mappers.attendance_out(state.record, repository.schedule_of(db, state.record), base_url),
        schedule=mappers.schedule_summary(state.schedule),
        auto_close_notices=[mappers.notice_out(notice) for notice in state.notices],
        clock_in_block=mappers.block_out(state.clock_in_block),
        can_self_schedule=state.can_self_schedule,
        branch=mappers.branch_out(state.branch),
    )


@router.post("/clock-in", response_model=EmployeeAttendanceOut)
def clock_in(
    schedule_id: str = Form(..., max_length=MAX_ID_LENGTH, description="The schedule shown by GET /attendance/state"),
    clock: tuple[Location, UploadedFile] = Depends(_clock_input),
    submission: clock_events.Submission | None = Depends(_submission),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_SELF_ATTENDANCE)),
):
    location, photo = clock
    try:
        record = clock_events.clock_in(db, user, schedule_id, location, photo, submission)
    except DomainError as error:
        raise _as_http(error) from error
    return mappers.attendance_out(record, repository.schedule_of(db, record), public_base_url())


@router.post("/clock-out", response_model=EmployeeAttendanceOut)
def clock_out(
    clock: tuple[Location, UploadedFile] = Depends(_clock_input),
    submission: clock_events.Submission | None = Depends(_submission),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_SELF_ATTENDANCE)),
):
    location, photo = clock
    try:
        record = clock_events.clock_out(db, user, location, photo, submission)
    except DomainError as error:
        raise _as_http(error) from error
    return mappers.attendance_out(record, repository.schedule_of(db, record), public_base_url())


@router.post("/auto-close-notices/ack", status_code=status.HTTP_204_NO_CONTENT)
def acknowledge_notices(
    ids: list[str] = Body(..., embed=True, max_length=MAX_NOTICE_IDS),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    service.acknowledge_notices(db, user, ids)
    db.commit()
