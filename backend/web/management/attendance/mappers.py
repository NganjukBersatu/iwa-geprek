"""Turns attendance entries into response schemas."""
from datetime import datetime

from app.core.http import static_url
from app.models.attendance import Attendance
from app.models.attendance_clock_event import CLOCK_IN, CLOCK_OUT, AttendanceClockEvent
from web.management.attendance.constants import LATE_SUBMISSION_AFTER
from web.management.attendance.domain import AttendanceEntry, AttendancePage
from web.management.attendance.schemas import AttendanceOut, AttendancePageOut, BranchPointOut, ProofOut


def _submission(events: tuple[AttendanceClockEvent, ...], kind: str) -> tuple[datetime | None, bool, bool]:
    """Kejadian terakhir dari jenis itu: kapan diterima server, apakah terlambat dikirim, dan apakah jamnya perlu ditinjau."""
    matching = [event for event in events if event.kind == kind]
    if not matching:
        return None, False, False
    event = matching[-1]
    return event.submitted_at, event.submitted_at - event.captured_at > LATE_SUBMISSION_AFTER, event.needs_review


def _clock_in_proof(record: Attendance, events: tuple[AttendanceClockEvent, ...], base_url: str) -> ProofOut:
    submitted_at, submitted_late, needs_review = _submission(events, CLOCK_IN)
    return ProofOut(
        photo_url=static_url(base_url, record.clock_in_photo_path),
        latitude=record.clock_in_latitude,
        longitude=record.clock_in_longitude,
        accuracy_meters=record.clock_in_accuracy,
        mode=record.clock_in_location_mode,
        note=record.clock_in_location_note,
        distance_meters=record.clock_in_distance_meters,
        radius_meters=record.clock_in_radius_meters,
        submitted_at=submitted_at,
        submitted_late=submitted_late,
        needs_review=needs_review,
    )


def _clock_out_proof(record: Attendance, events: tuple[AttendanceClockEvent, ...], base_url: str) -> ProofOut:
    submitted_at, submitted_late, needs_review = _submission(events, CLOCK_OUT)
    return ProofOut(
        photo_url=static_url(base_url, record.clock_out_photo_path),
        latitude=record.clock_out_latitude,
        longitude=record.clock_out_longitude,
        accuracy_meters=record.clock_out_accuracy,
        mode=record.clock_out_location_mode,
        note=record.clock_out_location_note,
        distance_meters=record.clock_out_distance_meters,
        radius_meters=record.clock_out_radius_meters,
        submitted_at=submitted_at,
        submitted_late=submitted_late,
        needs_review=needs_review,
    )


def _branch_point(entry: AttendanceEntry) -> BranchPointOut | None:
    if entry.branch_latitude is None or entry.branch_longitude is None:
        return None
    return BranchPointOut(latitude=entry.branch_latitude, longitude=entry.branch_longitude)


def attendance_out(entry: AttendanceEntry, base_url: str) -> AttendanceOut:
    record = entry.record
    user = entry.user
    return AttendanceOut(
        id=record.id,
        user_id=record.user_id,
        username=user.username,
        name=user.name,
        role_name=user.role.name if user.role else None,
        date=record.date,
        shift_code=entry.shift_code,
        shift_code_color=entry.shift_code_color,
        status=record.status,
        clock_in_at=record.clock_in_at,
        clock_out_at=record.clock_out_at,
        auto_closed=bool(record.auto_closed),
        schedule_id=record.schedule_id,
        note=record.note,
        outside_schedule_reason=record.outside_schedule_reason,
        clock_in=_clock_in_proof(record, entry.events, base_url),
        clock_out=_clock_out_proof(record, entry.events, base_url),
        branch_location=_branch_point(entry),
        late_minutes=entry.late_minutes,
        penalty=entry.penalty,
        work_minutes=entry.work_minutes,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def attendance_list_out(entries: list[AttendanceEntry], base_url: str) -> list[AttendanceOut]:
    return [attendance_out(entry, base_url) for entry in entries]


def attendance_page_out(page: AttendancePage, base_url: str) -> AttendancePageOut:
    return AttendancePageOut(items=attendance_list_out(page.entries, base_url), total=page.total, page=page.page, size=page.size)
