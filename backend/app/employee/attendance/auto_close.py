"""Menutup absen datang yang dibiarkan terbuka lama setelah shift selesai."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import as_aware
from app.employee.attendance import repository
from app.employee.attendance.policy import BranchPolicy
from app.employee.schedule.assignment import overtime_window, work_window


def close_expired(db: Session, user_id: str, now: datetime) -> int:
    """Jam pulang diisi jam selesai shift, dan batas tunggunya dihitung dari yang lebih akhir antara shift dan lembur terjadwal."""
    closed = 0
    for record in repository.open_present_records(db, user_id):
        schedule = repository.schedule_of(db, record)
        window = work_window(record.date, schedule, repository.code_by_id(db, record.shift_code_id))
        if window is None:
            continue
        shift_end = window[1]
        overtime = overtime_window(schedule) if schedule is not None else None
        last_end = max(shift_end, overtime[1]) if overtime is not None else shift_end
        if now >= last_end + BranchPolicy.load(db, record.outlet_id).auto_close_grace:
            record.clock_out_at = max(shift_end, as_aware(record.clock_in_at))
            record.auto_closed = True
            closed += 1
    return closed
