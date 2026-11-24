"""People: leave requests, empty schedules, attendance that did not happen or did not close, lateness, overtime, placement."""
from datetime import date, timedelta

from sqlalchemy import and_, exists, func, or_, select

from app.core import protection
from app.core.user_names import user_names
from app.employee.attendance.policy import BranchPolicy
from app.employee.schedule.assignment import work_window
from app.models.attendance import Attendance, AttendanceStatus
from app.models.day_off import DayOff
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.overtime import Overtime
from app.models.schedule import Schedule
from app.models.user import User
from web.management.issues import constants as c
from web.management.issues.domain import Issue, IssueKind, IssueLevel, Scope


# Someone deactivated or deleted no longer owes a shift, so their leftover schedule and old lateness raise nothing.
STILL_WORKING = select(User.id).where(User.is_active.is_(True))


def _ahead_level(scope: Scope, first: date) -> IssueLevel:
    return IssueLevel.PROBLEM if first <= scope.today + timedelta(days=c.SCHEDULE_URGENT_DAYS) else IssueLevel.WARNING


def leave_waiting(scope: Scope) -> list[Issue]:
    """A request without a branch belongs to every branch. day: first day asked, count: days asked."""
    branch = LeaveRequest.outlet_id.in_(scope.outlet_ids)
    rows = scope.db.scalars(
        select(LeaveRequest).where(LeaveRequest.status == LeaveStatus.PENDING, or_(branch, LeaveRequest.outlet_id.is_(None)) if scope.every_branch else branch)
    ).all()
    names = user_names(scope.db, (row.user_id for row in rows))
    return [
        Issue(
            IssueKind.LEAVE_WAITING,
            IssueLevel.PROBLEM,
            row.outlet_id,
            row.id,
            names.get(row.user_id, ""),
            day=row.start_date,
            at=row.created_at,
            count=(row.end_date - row.start_date).days + 1,
        )
        for row in rows
    ]


def schedule_ahead(scope: Scope) -> list[Issue]:
    """Days ahead, today included, where a person has neither a shift nor a day off anywhere (one per person), or a branch has no shift at all (one per branch).
    count: empty days, day: the first of them."""
    days = [scope.today + timedelta(days=offset) for offset in range(c.SCHEDULE_AHEAD_DAYS)]
    last = days[-1]
    people = scope.db.execute(
        select(User.id, User.outlet_id, func.coalesce(User.name, User.username)).where(
            User.is_active.is_(True), protection.schedulable(), User.outlet_id.in_(scope.outlet_ids)
        )
    ).all()
    person_ids = [person_id for person_id, _, _ in people]
    covered: set[tuple[str, date]] = set()
    usered: set[tuple[str, date]] = set()
    for user_id, outlet_id, day in scope.db.execute(
        select(Schedule.user_id, Schedule.outlet_id, Schedule.date).where(
            Schedule.date >= scope.today, Schedule.date <= last, or_(Schedule.user_id.in_(person_ids), Schedule.outlet_id.in_(scope.outlet_ids))
        )
    ).all():
        covered.add((user_id, day))
        usered.add((outlet_id, day))
    if person_ids:
        covered.update(
            scope.db.execute(select(DayOff.user_id, DayOff.date).where(DayOff.user_id.in_(person_ids), DayOff.date >= scope.today, DayOff.date <= last)).tuples().all()
        )

    issues: list[Issue] = []
    for person_id, outlet_id, name in people:
        empty = [day for day in days if (person_id, day) not in covered]
        if empty:
            issues.append(Issue(IssueKind.USER_UNSCHEDULED, _ahead_level(scope, empty[0]), outlet_id, person_id, name, day=empty[0], count=len(empty)))
    for outlet_id in scope.outlet_ids:
        empty = [day for day in days if (outlet_id, day) not in usered]
        if empty:
            issues.append(Issue(IssueKind.BRANCH_WITHOUT_USERS, _ahead_level(scope, empty[0]), outlet_id, None, "", day=empty[0], count=len(empty)))
    return issues


def no_clock_in(scope: Scope) -> list[Issue]:
    """A shift of the last days, today included once its start and the branch's late tolerance have passed, with no attendance mark
    and no approved leave. at: the start of the shift."""
    first = scope.first_day(c.EVENT_DAYS)
    marked = exists().where(Attendance.user_id == Schedule.user_id, Attendance.date == Schedule.date)
    on_leave = exists().where(
        LeaveRequest.user_id == Schedule.user_id,
        LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.start_date <= Schedule.date,
        LeaveRequest.end_date >= Schedule.date,
    )
    schedules = scope.db.scalars(
        select(Schedule).where(
            Schedule.outlet_id.in_(scope.outlet_ids),
            Schedule.date >= first,
            Schedule.date <= scope.today,
            Schedule.clock_in_used.is_(False),
            Schedule.user_id.in_(STILL_WORKING),
            ~marked,
            ~on_leave,
        )
    ).all()
    policies = BranchPolicy.load_many(scope.db, {schedule.outlet_id for schedule in schedules})
    issues: list[Issue] = []
    for schedule in schedules:
        if schedule.shift_code is not None and schedule.shift_code.is_day_off:
            continue
        window = work_window(schedule.date, schedule, schedule.shift_code)
        starts = window[0] if window else None
        if schedule.date == scope.today and (starts is None or starts + timedelta(minutes=policies[schedule.outlet_id].late_tolerance_minutes) > scope.now):
            continue
        name = schedule.user.name or schedule.user.username if schedule.user is not None else ""
        issues.append(Issue(IssueKind.NO_CLOCK_IN, IssueLevel.PROBLEM, schedule.outlet_id, schedule.id, name, day=schedule.date, at=starts))
    return issues


def attendance_left_open(scope: Scope) -> list[Issue]:
    """Clocked in on an earlier day of the last days and never out (a warning), or closed by the system (a notice)."""
    rows = scope.db.scalars(
        select(Attendance).where(
            Attendance.outlet_id.in_(scope.outlet_ids),
            Attendance.date >= scope.first_day(c.EVENT_DAYS),
            or_(Attendance.auto_closed.is_(True), and_(Attendance.clock_in_at.is_not(None), Attendance.clock_out_at.is_(None), Attendance.date < scope.today)),
        )
    ).all()
    names = user_names(scope.db, (row.user_id for row in rows))
    return [
        Issue(
            IssueKind.AUTO_CLOSED if row.auto_closed else IssueKind.NO_CLOCK_OUT,
            IssueLevel.NOTICE if row.auto_closed else IssueLevel.WARNING,
            row.outlet_id,
            row.id,
            names.get(row.user_id, ""),
            day=row.date,
            at=row.clock_in_at,
        )
        for row in rows
    ]


def late_repeated(scope: Scope) -> list[Issue]:
    """count: late arrivals in the window."""
    rows = scope.db.execute(
        select(Attendance.user_id, Attendance.outlet_id, func.count(Attendance.id))
        .where(
            Attendance.outlet_id.in_(scope.outlet_ids),
            Attendance.status == AttendanceStatus.LATE,
            Attendance.date >= scope.first_day(c.LATE_REPEATED_DAYS),
            Attendance.user_id.in_(STILL_WORKING),
        )
        .group_by(Attendance.user_id, Attendance.outlet_id)
        .having(func.count(Attendance.id) >= c.LATE_REPEATED_COUNT)
    ).all()
    names = user_names(scope.db, (user_id for user_id, _, _ in rows))
    return [Issue(IssueKind.LATE_REPEATED, IssueLevel.WARNING, outlet_id, user_id, names.get(user_id, ""), count=count) for user_id, outlet_id, count in rows]


def overtime_left_open(scope: Scope) -> list[Issue]:
    """Overtime of an earlier day of the last days that never ended. at: when it started."""
    rows = scope.db.scalars(
        select(Overtime).where(
            Overtime.outlet_id.in_(scope.outlet_ids), Overtime.end_at.is_(None), Overtime.date >= scope.first_day(c.EVENT_DAYS), Overtime.date < scope.today
        )
    ).all()
    names = user_names(scope.db, (row.user_id for row in rows))
    return [Issue(IssueKind.OVERTIME_OPEN, IssueLevel.WARNING, row.outlet_id, row.id, names.get(row.user_id, ""), day=row.date, at=row.start_at) for row in rows]


def user_unplaced(scope: Scope) -> list[Issue]:
    """Active people who can be scheduled but have no branch; only asked about with every branch, since they belong to none."""
    if not scope.every_branch:
        return []
    rows = scope.db.execute(
        select(User.id, func.coalesce(User.name, User.username)).where(User.is_active.is_(True), protection.schedulable(), User.outlet_id.is_(None))
    ).all()
    return [Issue(IssueKind.USER_UNPLACED, IssueLevel.SUGGESTION, None, user_id, name) for user_id, name in rows]
