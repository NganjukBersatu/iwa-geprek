"""Builds the monthly summary: recorded days, absences implied by the schedule, and the totals."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.clock import as_aware, now
from app.core.period import month_bounds
from app.employee.attendance import repository as attendance_repository
from app.employee.attendance.lateness import minutes_late
from app.employee.attendance.policy import BranchPolicy
from app.employee.attendance.summary import repository
from app.employee.attendance.summary.domain import Day, Summary, Totals
from app.employee.attendance.work_time import worked_minutes
from app.employee.overtime.ledger import merged_minutes, month_entries
from app.employee.schedule.assignment import work_window
from app.models.attendance import PRESENT_STATUSES, Attendance, AttendanceStatus
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode
from app.models.user import User


def _role_name(schedule: Schedule | None) -> str | None:
    return schedule.role.name if schedule is not None and schedule.role is not None else None


def _recorded_day(policy: BranchPolicy, record: Attendance, schedule: Schedule | None, code: ShiftCode | None) -> Day:
    present = record.status in PRESENT_STATUSES and record.clock_in_at is not None
    late = 0
    window = None
    if present and record.clock_in_at is not None:
        window = work_window(record.date, schedule, code)
        late = minutes_late(record.clock_in_at, window[0]) if window is not None else 0
    return Day(
        date=record.date,
        status=record.status,
        automatic=False,
        record=record,
        code=code.code if code else None,
        role_name=_role_name(schedule),
        late_minutes=late,
        work_minutes=worked_minutes(record, window) if present else None,
        penalty=policy.penalty(late),
    )


def _has_ended(schedule: Schedule, code: ShiftCode | None, today: date) -> bool:
    """Alfa baru dihitung setelah jam selesai shift lewat, bukan sekadar tanggalnya terlewat, supaya shift malam yang masih berjalan tidak dianggap alfa."""
    if schedule.date >= today:
        return False
    window = work_window(schedule.date, schedule, code)
    return window is None or as_aware(window[1]) <= now()


def _implied_absence(schedule: Schedule) -> Day:
    code = schedule.shift_code
    return Day(
        date=schedule.date,
        status=AttendanceStatus.ABSENT,
        automatic=True,
        record=None,
        code=code.code if code else None,
        role_name=_role_name(schedule),
        late_minutes=0,
        work_minutes=None,
        penalty=0,
    )


def _totals(days: list[Day], scheduled: int, overtime_minutes: int) -> Totals:
    def count(status: AttendanceStatus) -> int:
        return sum(1 for day in days if day.status == status)

    return Totals(
        scheduled=scheduled,
        present=count(AttendanceStatus.PRESENT),
        late=count(AttendanceStatus.LATE),
        leave=count(AttendanceStatus.PERMIT),
        sick=count(AttendanceStatus.SICK),
        absent=count(AttendanceStatus.ABSENT),
        work_minutes=sum(day.work_minutes or 0 for day in days),
        late_minutes=sum(day.late_minutes for day in days),
        overtime_minutes=overtime_minutes,
        penalty=sum(day.penalty for day in days),
    )


def build_days_many(db: Session, user_ids: list[str], first: date, last: date, today: date) -> dict[str, tuple[list[Day], int]]:
    """The recorded days of the range plus the absences each person's schedule implies, and how many schedules each holds.

    A scheduled day that has already passed with no record counts as absent; today is never counted. The records, the schedules,
    the codes, and the branch rules are read once for everybody, so the number of queries does not depend on the number of people.
    """
    records = repository.records_between(db, user_ids, first, last)
    schedules = repository.schedules_between(db, user_ids, first, last)
    schedule_by_id = {schedule.id: schedule for schedule in schedules}
    code_ids = {record.shift_code_id for record in records if record.shift_code_id}
    code_ids |= {schedule.shift_code_id for schedule in schedules if schedule.shift_code_id}
    codes = repository.codes_by_id(db, code_ids)
    policies = BranchPolicy.load_many(db, {record.outlet_id for record in records})

    records_of: dict[str, list[Attendance]] = {user_id: [] for user_id in user_ids}
    for record in records:
        records_of[record.user_id].append(record)
    schedules_of: dict[str, list[Schedule]] = {user_id: [] for user_id in user_ids}
    for schedule in schedules:
        schedules_of[schedule.user_id].append(schedule)

    built: dict[str, tuple[list[Day], int]] = {}
    for user_id in user_ids:
        mine, planned = records_of[user_id], schedules_of[user_id]
        days = [
            _recorded_day(
                policies[record.outlet_id],
                record,
                (schedule_by_id.get(record.schedule_id) if record.schedule_id else None) or attendance_repository.schedule_of(db, record),
                codes.get(record.shift_code_id) if record.shift_code_id else None,
            )
            for record in mine
        ]
        recorded = {(record.date, record.shift_code_id) for record in mine}
        days += [
            _implied_absence(schedule)
            for schedule in planned
            if _has_ended(schedule, codes.get(schedule.shift_code_id) if schedule.shift_code_id else None, today)
            and (schedule.date, schedule.shift_code_id) not in recorded
        ]
        days.sort(key=lambda day: (day.date, day.code or ""))
        built[user_id] = (days, len(planned))
    return built


def build_days(db: Session, user: User, first: date, last: date, today: date) -> tuple[list[Day], int]:
    return build_days_many(db, [user.id], first, last, today)[user.id]


def build_summary(db: Session, user: User, month_start: date, today: date) -> Summary:
    first, last = month_bounds(month_start)
    days, scheduled = build_days(db, user, first, last, today)
    overtime_minutes = merged_minutes(month_entries(db, user.id, first, last))
    return Summary(
        month_start=first,
        until=min(last, today),
        totals=_totals(days, scheduled, overtime_minutes),
        days=days,
    )
