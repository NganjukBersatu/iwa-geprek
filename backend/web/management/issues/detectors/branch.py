"""Branch operations: outlet and daily tasks not done, and tablets that went quiet."""
from datetime import date, timedelta

from sqlalchemy import func, select

from app.core.clock import as_aware
from app.employee.batches.recurrence import applies_on
from app.employee.batches.service import window_of
from app.models.attendance import Attendance
from app.models.device import REGISTERED, Device
from app.models.outlet_batch import KIND_ROUTINE, SHARED_FILLER, OutletBatch, OutletBatchRun
from app.models.schedule import Schedule
from web.management.devices.constants import WAITING_STATUS
from web.management.issues import constants as c
from web.management.issues.domain import Issue, IssueKind, IssueLevel, Scope


def _scheduled(scope: Scope, batches: list[OutletBatch], first: date) -> dict[tuple[str, date], set[str]]:
    """Staf yang dijadwalkan per kode shift dan hari, hanya untuk kode shift yang dipakai tugas rutin."""
    code_ids = {code.id for batch in batches if batch.kind == KIND_ROUTINE and not batch.for_named_user for code in batch.shift_codes}
    if not code_ids:
        return {}
    rows = scope.db.execute(
        select(Schedule.shift_code_id, Schedule.date, Schedule.user_id).where(
            Schedule.outlet_id.in_(scope.outlet_ids), Schedule.date >= first, Schedule.shift_code_id.in_(code_ids)
        )
    ).all()
    found: dict[tuple[str, date], set[str]] = {}
    for code_id, day, user_id in rows:
        found.setdefault((code_id, day), set()).add(user_id)
    return found


def _attended(scope: Scope, first: date) -> set[tuple[str, date]]:
    rows = scope.db.execute(
        select(Attendance.user_id, Attendance.date).where(
            Attendance.outlet_id.in_(scope.outlet_ids), Attendance.date >= first, Attendance.clock_in_at.is_not(None)
        )
    ).all()
    return {(user_id, day) for user_id, day in rows}


def _missed(batch: OutletBatch, day: date, done: set[tuple[str, date, str]], scheduled: dict[tuple[str, date], set[str]], attended: set[tuple[str, date]]) -> bool:
    """Tugas outlet terlewat bila tidak ada pengisian; tugas rutin hanya jatuh tempo bila ada yang dijadwalkan di shiftnya hari itu."""
    if batch.kind != KIND_ROUTINE:
        return (batch.id, day, SHARED_FILLER) not in done
    if batch.for_named_user:
        # Orang yang ditunjuk tidak terikat jadwal, jadi tugasnya jatuh tempo hanya pada hari ia hadir.
        due = {person.id for person in batch.recipients if (person.id, day) in attended}
    else:
        due = set().union(*(scheduled.get((code.id, day), set()) for code in batch.shift_codes))
    if not batch.each_fills:
        return bool(due) and (batch.id, day, SHARED_FILLER) not in done
    # Yang dijadwalkan tetapi tidak datang tidak dihitung, karena ketidakhadirannya sudah dilaporkan tersendiri.
    return any((user_id, day) in attended and (batch.id, day, user_id) not in done for user_id in due)


def tasks_missed(scope: Scope) -> list[Issue]:
    """Days of the last days whose task range has ended without the run it needs; a task counts only from the day it was made. One per task; count: days missed, day: the latest."""
    first = scope.first_day(c.EVENT_DAYS)
    batches = list(scope.db.scalars(select(OutletBatch).where(OutletBatch.is_active.is_(True), OutletBatch.outlet_id.in_(scope.outlet_ids))).all())
    if not batches:
        return []
    done = set(
        scope.db.execute(
            select(OutletBatchRun.batch_id, OutletBatchRun.day, OutletBatchRun.filler_key).where(
                OutletBatchRun.batch_id.in_([batch.id for batch in batches]), OutletBatchRun.day >= first, OutletBatchRun.cancelled_at.is_(None)
            )
        )
        .tuples()
        .all()
    )
    scheduled = _scheduled(scope, batches, first)
    attended = _attended(scope, first) if any(batch.each_fills or batch.for_named_user for batch in batches) else set()
    days = [first + timedelta(days=offset) for offset in range(c.EVENT_DAYS)]
    issues: list[Issue] = []
    for batch in batches:
        missed: list[date] = []
        for day in days:
            start, end = window_of(batch, day)
            if applies_on(batch, day) and end <= scope.now and start >= as_aware(batch.created_at) and _missed(batch, day, done, scheduled, attended):
                missed.append(day)
        if missed:
            issues.append(Issue(IssueKind.TASK_MISSED, IssueLevel.WARNING, batch.outlet_id, batch.id, batch.name, day=missed[-1], count=len(missed)))
    return issues


def quiet_devices(scope: Scope) -> list[Issue]:
    """Registered tablets unused for the window (at: last use), and pairing codes that expired before anyone used them (at: expiry)."""
    last_seen = func.coalesce(Device.last_used_at, Device.paired_at, Device.created_at)
    idle = scope.db.execute(
        select(Device.id, Device.outlet_id, Device.name, last_seen).where(
            Device.outlet_id.in_(scope.outlet_ids), Device.status == REGISTERED, last_seen < scope.now - timedelta(days=c.DEVICE_IDLE_DAYS)
        )
    ).all()
    expired = scope.db.execute(
        select(Device.id, Device.outlet_id, Device.name, Device.code_expires_at).where(
            Device.outlet_id.in_(scope.outlet_ids), Device.status == WAITING_STATUS, Device.code_expires_at < scope.now
        )
    ).all()
    return [
        *(Issue(IssueKind.DEVICE_IDLE, IssueLevel.NOTICE, outlet_id, device_id, name, at=at) for device_id, outlet_id, name, at in idle),
        *(Issue(IssueKind.DEVICE_CODE_EXPIRED, IssueLevel.NOTICE, outlet_id, device_id, name, at=at) for device_id, outlet_id, name, at in expired),
    ]
