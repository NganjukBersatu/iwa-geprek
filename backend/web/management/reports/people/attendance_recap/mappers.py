"""Turns the attendance recap into its response schema."""
from web.management.reports.people.attendance_recap.domain import AttendanceRecap
from web.management.reports.people.attendance_recap.schemas import AttendanceRecapOut


def attendance_recap_out(recap: AttendanceRecap) -> AttendanceRecapOut:
    return AttendanceRecapOut.model_validate(recap)
