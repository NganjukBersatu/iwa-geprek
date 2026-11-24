"""Database reads and small writes for batches."""
from collections.abc import Iterable
from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.outlet_batch import SHARED_FILLER, OutletBatch, OutletBatchAnswer, OutletBatchRun, OutletBatchRunVersion
from app.models.schedule import Schedule
from app.models.task import Task


def find_batch(db: Session, batch_id: str) -> OutletBatch | None:
    return db.get(OutletBatch, batch_id)


def active_batches(db: Session, outlet_ids: Iterable[str]) -> list[OutletBatch]:
    return list(
        db.scalars(
            select(OutletBatch)
            .where(OutletBatch.outlet_id.in_(list(outlet_ids)), OutletBatch.is_active.is_(True))
            .order_by(OutletBatch.start_clock, OutletBatch.sort_order)
        ).all()
    )


def attendances_of(db: Session, user_id: str, day: date) -> list[Attendance]:
    """The days a person actually arrived; a row without a clock-in time is a permit or an absence."""
    return list(
        db.scalars(
            select(Attendance).where(
                Attendance.user_id == user_id, Attendance.date == day, Attendance.clock_in_at.is_not(None)
            )
        ).all()
    )


def scheduled_shift_codes(db: Session, user_id: str, day: date) -> set[str]:
    """Kode shift yang dijadwalkan untuk orang ini pada hari itu, di cabang mana pun."""
    rows = db.scalars(
        select(Schedule.shift_code_id).where(Schedule.user_id == user_id, Schedule.date == day, Schedule.shift_code_id.is_not(None))
    ).all()
    return {row for row in rows if row}


def runs_of(db: Session, batch_ids: Iterable[str], day: date, user_id: str) -> dict[str, OutletBatchRun]:
    """Pengisian yang berlaku bagi orang ini: milik bersama, atau miliknya sendiri untuk tugas yang diisi tiap orang."""
    ids = list(batch_ids)
    if not ids:
        return {}
    rows = db.scalars(
        select(OutletBatchRun).where(
            OutletBatchRun.batch_id.in_(ids),
            OutletBatchRun.day == day,
            OutletBatchRun.filler_key.in_((SHARED_FILLER, user_id)),
            OutletBatchRun.cancelled_at.is_(None),
        )
    ).all()
    return {row.batch_id: row for row in rows}


def locked_run(db: Session, run_id: str) -> OutletBatchRun | None:
    """Dikunci supaya dua perbaikan yang datang bersamaan tidak saling menimpa."""
    return db.scalars(select(OutletBatchRun).where(OutletBatchRun.id == run_id).with_for_update()).first()


def find_run(db: Session, run_id: str) -> OutletBatchRun | None:
    return db.get(OutletBatchRun, run_id)


def cancelled_run(db: Session, batch_id: str, day: date, filler_key: str) -> OutletBatchRun | None:
    """Pengisian yang dibatalkan untuk tempat yang sama; barisnya dipakai lagi saat tugasnya diisi ulang."""
    return db.scalars(
        select(OutletBatchRun)
        .where(
            OutletBatchRun.batch_id == batch_id,
            OutletBatchRun.day == day,
            OutletBatchRun.filler_key == filler_key,
            OutletBatchRun.cancelled_at.is_not(None),
        )
        .with_for_update()
    ).first()


def answers_of_run(db: Session, run_id: str) -> list[OutletBatchAnswer]:
    return list(db.scalars(select(OutletBatchAnswer).where(OutletBatchAnswer.run_id == run_id).order_by(OutletBatchAnswer.id)).all())


def followed_up(db: Session, run_ids: Iterable[str]) -> set[str]:
    """Pengisian yang sudah punya tugas tindak lanjut, dalam satu query."""
    wanted = [run_id for run_id in run_ids if run_id]
    if not wanted:
        return set()
    return set(db.scalars(select(Task.source_run_id).where(Task.source_run_id.in_(wanted)).distinct()).all())


def version_photo_paths(db: Session, run_id: str) -> list[str]:
    """Foto yang hanya dirujuk versi lama, untuk dibuang saat pengisiannya dihapus permanen."""
    versions = db.scalars(select(OutletBatchRunVersion.answers).where(OutletBatchRunVersion.run_id == run_id)).all()
    return [path for answers in versions for answer in answers if (path := answer.get("photo_path"))]


def drop_versions(db: Session, run_id: str) -> None:
    db.execute(delete(OutletBatchRunVersion).where(OutletBatchRunVersion.run_id == run_id))


def next_version_number(db: Session, run_id: str) -> int:
    return (db.scalar(select(func.max(OutletBatchRunVersion.number)).where(OutletBatchRunVersion.run_id == run_id)) or 0) + 1
