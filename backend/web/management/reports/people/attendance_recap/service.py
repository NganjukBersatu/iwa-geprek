"""Builds the attendance recap of everyone in a range, from the same day rules the app's own summary uses.

A scheduled day that already passed with no record counts as absent; it is worked out, never written, so an admin who
hears later only has to mark it as leave or sick. The penalty is information only: nothing here pays anyone.
"""
from dataclasses import replace
from datetime import date

from sqlalchemy.orm import Session

from app.core.clock import minutes_between, today
from app.core.money import round_rupiah
from app.core.sorting import RowSorting
from app.employee.attendance.policy import BranchPolicy
from app.employee.attendance.summary.domain import Day
from app.employee.attendance.summary.service import build_days_many
from app.employee.overtime.ledger import merged_minutes, month_entries_many
from app.models.attendance import AttendanceStatus
from app.models.user import User
from web.management.reports.common import month_to_date
from web.management.reports.people.attendance_recap import repository
from web.management.reports.people.attendance_recap.domain import AttendanceRecap, RecapDay, RecapOvertime, RecapRule, UserRecap


STATUS_ORDER = list(AttendanceStatus)

USER_SORTING: RowSorting[UserRecap] = RowSorting(
    keys={
        "user": lambda row: (row.name or "").strip() or row.username,
        "scheduled": lambda row: row.scheduled,
        "present": lambda row: row.present,
        "late": lambda row: row.late,
        "leave": lambda row: row.leave,
        "sick": lambda row: row.sick,
        "absent": lambda row: row.absent,
        "work_minutes": lambda row: row.work_minutes,
        "late_minutes": lambda row: row.late_minutes,
        "penalty": lambda row: row.penalty,
        "overtime_minutes": lambda row: row.overtime_minutes,
    },
    identity=lambda row: row.user_id,
)

DAY_SORTING: RowSorting[RecapDay] = RowSorting(
    keys={
        "date": lambda row: row.date,
        "code": lambda row: row.code,
        "status": lambda row: STATUS_ORDER.index(row.status),
        "clock_in": lambda row: row.clock_in_at,
        "clock_out": lambda row: row.clock_out_at,
        "work_minutes": lambda row: row.work_minutes,
        "late_minutes": lambda row: row.late_minutes,
        "penalty": lambda row: row.penalty,
        "note": lambda row: row.note,
    },
    identity=lambda row: f"{row.date.isoformat()}|{row.code or ''}",
)

OVERTIME_SORTING: RowSorting[RecapOvertime] = RowSorting(
    keys={
        "date": lambda row: row.date,
        "kind": lambda row: row.scheduled,
        "start": lambda row: row.start_at,
        "end": lambda row: row.end_at,
        "minutes": lambda row: row.minutes,
        "note": lambda row: row.note,
    },
    identity=lambda row: row.id,
)


def sorted_recap(recap: AttendanceRecap, sort: str | None, day_sort: str | None, overtime_sort: str | None) -> AttendanceRecap:
    """Every person's days and overtime follow the same order, so each detail opened reads alike."""
    user = [
        replace(row, days=DAY_SORTING.apply(row.days, day_sort), overtime=OVERTIME_SORTING.apply(row.overtime, overtime_sort))
        for row in recap.user
    ]
    return replace(recap, user=USER_SORTING.apply(user, sort))


def _recap_day(day: Day) -> RecapDay:
    record = day.record
    return RecapDay(
        date=day.date,
        code=day.code,
        status=day.status,
        automatic=day.automatic,
        clock_in_at=record.clock_in_at if record else None,
        clock_out_at=record.clock_out_at if record else None,
        late_minutes=day.late_minutes,
        work_minutes=day.work_minutes,
        penalty=day.penalty,
        note=record.note if record else None,
    )


def _user_recap(user: User, days: list[Day], scheduled: int, entries: list) -> UserRecap:

    def count(status: AttendanceStatus) -> int:
        return sum(1 for day in days if day.status == status)

    return UserRecap(
        user_id=user.id,
        username=user.username,
        name=user.name,
        scheduled=scheduled,
        present=count(AttendanceStatus.PRESENT),
        late=count(AttendanceStatus.LATE),
        leave=count(AttendanceStatus.PERMIT),
        sick=count(AttendanceStatus.SICK),
        absent=count(AttendanceStatus.ABSENT),
        automatic_absences=sum(1 for day in days if day.automatic),
        work_minutes=sum(day.work_minutes or 0 for day in days),
        late_minutes=sum(day.late_minutes for day in days),
        penalty=sum(day.penalty for day in days),
        overtime_minutes=merged_minutes(entries),
        days=[_recap_day(day) for day in days],
        overtime=[RecapOvertime(entry.id, entry.date, entry.start_at, entry.end_at, minutes_between(entry.start_at, entry.end_at) or 0, entry.scheduled, entry.note) for entry in entries],
    )


def attendance_recap(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> AttendanceRecap:
    """The rule shown belongs to the chosen branch, or to the first branch when all of them are shown."""
    first, last = month_to_date(start, end)
    current = today()
    people = repository.user_with_activity(db, first, last, outlet_id)
    ids = [user.id for user in people]
    days_of, entries_of = build_days_many(db, ids, first, last, current), month_entries_many(db, ids, first, last)
    recaps = [_user_recap(user, days_of[user.id][0], days_of[user.id][1], entries_of[user.id]) for user in people]
    policy = BranchPolicy.load(db, outlet_id or repository.first_outlet_id(db) or "")
    work_minutes = sum(recap.work_minutes for recap in recaps)
    revenue = repository.revenue(db, first, last, outlet_id)
    return AttendanceRecap(
        start=first,
        end=last,
        rule=RecapRule(policy.late_tolerance_minutes, policy.late_penalty_per_minute),
        total_penalty=sum(recap.penalty for recap in recaps),
        total_late_minutes=sum(recap.late_minutes for recap in recaps),
        total_overtime_minutes=sum(recap.overtime_minutes for recap in recaps),
        total_absent=sum(recap.absent for recap in recaps),
        total_attended=sum(recap.present + recap.late for recap in recaps),
        total_work_minutes=work_minutes,
        total_revenue=revenue,
        revenue_per_work_hour=round_rupiah(revenue * 60 / work_minutes) if work_minutes > 0 else None,
        user=recaps,
    )
