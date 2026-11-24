"""Absen datang dan pulang dari antrean app: kunci idempotensi, waktu ambil yang dijepit, dan jejak pengirimannya."""
import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import as_aware, now
from app.core.errors import DomainError
from app.core.uploads import UploadedFile
from app.employee.attendance import messages, service
from app.employee.attendance.constants import CLOCK_SKEW, MAX_OFFLINE_AGE
from app.employee.attendance.location_validation import Location
from app.models.attendance import Attendance
from app.models.attendance_clock_event import (
    CLOCK_IN,
    CLOCK_OUT,
    SOURCE_DEVICE_CLOCK,
    SOURCE_SERVER_ANCHORED,
    AttendanceClockEvent,
)
from app.models.user import User

TIME_SOURCES = frozenset({SOURCE_SERVER_ANCHORED, SOURCE_DEVICE_CLOCK})
FIELD_SEPARATOR = "\x1f"


@dataclass(frozen=True)
class Submission:
    """Yang dibawa absen dari antrean: kunci pengiriman, waktu ambil, dan sumber waktu itu; waktu ambil kosong berarti absen langsung."""

    key: str
    captured_at: datetime | None
    time_source: str


@dataclass(frozen=True)
class ClockRequest:
    schedule_id: str | None
    location: Location
    photo: UploadedFile


def effective_time(captured_at: datetime | None, current: datetime) -> datetime:
    """Waktu yang dipakai semua aturan absen: waktu ambil, tidak pernah di masa depan dan tidak lebih tua dari batas usia."""
    if captured_at is None:
        return current
    captured = as_aware(captured_at)
    if captured > current + CLOCK_SKEW:
        raise DomainError(messages.CAPTURED_IN_FUTURE, code="CAPTURED_IN_FUTURE")
    if current - captured > MAX_OFFLINE_AGE:
        raise DomainError(messages.CAPTURED_TOO_OLD, code="CAPTURED_TOO_OLD")
    return min(captured, current)


def _digest(kind: str, request: ClockRequest) -> str:
    """Sidik isi absen tanpa waktu ambil dan sumber waktunya, karena itu metadata: absen yang sama boleh dikirim langsung lalu diulang dari antrean."""
    location = request.location
    fields = (
        kind,
        request.schedule_id or "",
        repr(location.latitude),
        repr(location.longitude),
        repr(location.accuracy),
        location.mode,
        location.note or "",
        hashlib.sha256(request.photo.content).hexdigest(),
    )
    return hashlib.sha256(FIELD_SEPARATOR.join(fields).encode("utf-8")).hexdigest()


def _stored(db: Session, user_id: str, key: str, digest: str) -> Attendance | None:
    """Hasil kiriman yang sama bila kuncinya sudah dipakai; kunci yang sama dengan isi berbeda ditolak."""
    event = db.scalar(
        select(AttendanceClockEvent).where(AttendanceClockEvent.user_id == user_id, AttendanceClockEvent.idempotency_key == key)
    )
    if event is None:
        return None
    if event.request_hash != digest:
        raise DomainError(messages.KEY_REUSED, status=HTTPStatus.CONFLICT, code="IDEMPOTENCY_KEY_REUSED")
    return db.get(Attendance, event.attendance_id)


def _submit(
    db: Session,
    user: User,
    kind: str,
    submission: Submission | None,
    request: ClockRequest,
    action: Callable[[datetime], Attendance],
) -> Attendance:
    current = now()
    if submission is None:
        record = action(current)
        db.commit()
        db.refresh(record)
        return record

    user_id = user.id
    digest = _digest(kind, request)
    stored = _stored(db, user_id, submission.key, digest)
    if stored is not None:
        return stored

    instant = effective_time(submission.captured_at, current)
    try:
        record = action(instant)
    except DomainError:
        # Dua kiriman berkunci sama yang bersamaan: yang kalah mendapat hasil pemenang, bukan galat.
        db.rollback()
        stored = _stored(db, user_id, submission.key, digest)
        if stored is not None:
            return stored
        raise
    db.add(
        AttendanceClockEvent(
            captured_at=instant,
            submitted_at=current,
            needs_review=submission.time_source == SOURCE_DEVICE_CLOCK,
            user_id=user_id,
            attendance_id=record.id,
            idempotency_key=submission.key,
            kind=kind,
            time_source=submission.time_source,
            request_hash=digest,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        stored = _stored(db, user_id, submission.key, digest)
        if stored is not None:
            return stored
        raise
    db.refresh(record)
    return record


def clock_in(
    db: Session, user: User, schedule_id: str, location: Location, photo: UploadedFile, submission: Submission | None
) -> Attendance:
    request = ClockRequest(schedule_id, location, photo)
    return _submit(
        db, user, CLOCK_IN, submission, request, lambda instant: service.clock_in(db, user, schedule_id, location, photo, instant)
    )


def clock_out(db: Session, user: User, location: Location, photo: UploadedFile, submission: Submission | None) -> Attendance:
    request = ClockRequest(None, location, photo)
    return _submit(db, user, CLOCK_OUT, submission, request, lambda instant: service.clock_out(db, user, location, photo, instant))
