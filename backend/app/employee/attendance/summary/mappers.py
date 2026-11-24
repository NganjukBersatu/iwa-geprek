"""Turns the summary into its response schema."""
from app.core.period import month_label
from app.employee.attendance.constants import LOCATION_MODE_FROM_STORED
from app.employee.attendance.mappers import photo_url
from app.employee.attendance.summary.domain import Day, Summary
from app.employee.attendance.summary.schemas import DayOut, LocationOut, AttendanceSummaryOut, TotalsOut
from app.models.attendance import Attendance


def _mode(stored: str | None) -> str | None:
    return LOCATION_MODE_FROM_STORED.get(stored, stored) if stored else None


def _in_location(record: Attendance) -> LocationOut:
    return LocationOut(
        mode=_mode(record.clock_in_location_mode),
        note=record.clock_in_location_note,
        distance_meters=record.clock_in_distance_meters,
        accuracy_meters=record.clock_in_accuracy,
        radius_meters=record.clock_in_radius_meters,
    )


def _out_location(record: Attendance) -> LocationOut:
    return LocationOut(
        mode=_mode(record.clock_out_location_mode),
        note=record.clock_out_location_note,
        distance_meters=record.clock_out_distance_meters,
        accuracy_meters=record.clock_out_accuracy,
        radius_meters=record.clock_out_radius_meters,
    )


def day_out(day: Day, base_url: str) -> DayOut:
    record = day.record
    return DayOut(
        date=day.date,
        status=day.status.value,
        automatic=day.automatic,
        shift_code=day.code,
        role_name=day.role_name,
        clock_in_at=record.clock_in_at if record else None,
        clock_out_at=record.clock_out_at if record else None,
        late_minutes=day.late_minutes,
        work_minutes=day.work_minutes,
        penalty=day.penalty,
        note=record.note if record else None,
        outside_schedule_reason=record.outside_schedule_reason if record else None,
        auto_closed=bool(record and record.auto_closed),
        clock_in_photo_url=photo_url(base_url, record.clock_in_photo_path, record.clock_in_at is not None) if record else None,
        clock_out_photo_url=photo_url(base_url, record.clock_out_photo_path, record.clock_out_at is not None) if record else None,
        clock_in_location=_in_location(record) if record else None,
        clock_out_location=_out_location(record) if record else None,
    )


def summary_out(summary: Summary, base_url: str) -> AttendanceSummaryOut:
    return AttendanceSummaryOut(
        month=month_label(summary.month_start),
        until=summary.until,
        totals=TotalsOut(**vars(summary.totals)),
        days=[day_out(day, base_url) for day in summary.days],
    )
