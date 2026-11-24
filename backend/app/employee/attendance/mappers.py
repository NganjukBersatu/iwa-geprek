"""Turns database rows into response schemas."""
from app.core.http import static_url
from app.employee.attendance.clock_in_block import ClockInBlock
from app.employee.attendance.schemas import EmployeeAttendanceOut, AutoCloseNotice, AttendanceBranchOut, ClockInBlockOut, ScheduleSummary
from app.employee.attendance.service import Notice
from app.employee.attendance.work_time import worked_minutes
from app.employee.schedule.assignment import work_window
from app.models.attendance import Attendance
from app.models.outlet import Outlet
from app.models.schedule import Schedule


def schedule_summary(schedule: Schedule | None) -> ScheduleSummary | None:
    if schedule is None:
        return None
    code = schedule.shift_code
    return ScheduleSummary(
        id=schedule.id,
        date=schedule.date,
        code=code.code if code else None,
        color=code.color if code else None,
        starts_at=schedule.starts_at,
        ends_at=schedule.ends_at,
    )


def photo_url(base_url: str, path: str | None, present: bool) -> str | None:
    return static_url(base_url, path) if present else None


def attendance_out(record: Attendance | None, schedule: Schedule | None, base_url: str) -> EmployeeAttendanceOut | None:
    if record is None:
        return None
    return EmployeeAttendanceOut(
        id=record.id,
        date=record.date,
        status=record.status.value if record.status else "",
        clock_in_at=record.clock_in_at,
        clock_out_at=record.clock_out_at,
        auto_closed=record.auto_closed,
        clock_in_photo_url=photo_url(base_url, record.clock_in_photo_path, record.clock_in_at is not None),
        clock_out_photo_url=photo_url(base_url, record.clock_out_photo_path, record.clock_out_at is not None),
        schedule=schedule_summary(schedule),
        work_minutes=worked_minutes(
            record, work_window(record.date, schedule, schedule.shift_code if schedule else None)
        ),
    )


def branch_out(branch: Outlet | None) -> AttendanceBranchOut | None:
    if branch is None:
        return None
    return AttendanceBranchOut(
        id=branch.id,
        name=branch.name,
        latitude=branch.latitude,
        longitude=branch.longitude,
        radius_meters=branch.attendance_radius_meters,
    )


def block_out(block: ClockInBlock | None) -> ClockInBlockOut | None:
    if block is None:
        return None
    return ClockInBlockOut(reason=block.reason, schedule=schedule_summary(block.schedule), at=block.at)


def notice_out(notice: Notice) -> AutoCloseNotice:
    record = notice.record
    return AutoCloseNotice(
        id=record.id,
        date=record.date,
        code=notice.code.code if notice.code else None,
        clock_in_at=record.clock_in_at,
        clock_out_at=record.clock_out_at,
    )
