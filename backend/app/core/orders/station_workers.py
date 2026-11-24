"""Karyawan yang boleh dicatat sebagai pelaku satu menu di stasiun: akun yang login di tablet, ditambah yang sedang bekerja di cabang itu dengan peran yang dibolehkan untuk stasiun tersebut."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models.attendance import PRESENT_STATUSES, Attendance
from app.models.role import Role
from app.models.schedule import Schedule
from app.models.user import User
from app.models.station import StationBranchRole, StationRole

MAX_WORKERS = 50
CONFLICT = 409

NOT_ELIGIBLE = "Karyawan itu tidak bisa dipilih untuk stasiun ini. Pilih dari daftar, lalu coba lagi."


@dataclass(frozen=True)
class Worker:
    user_id: str
    name: str
    role_name: str | None
    # Kosong untuk akun yang login bila belum absen masuk.
    clock_in_at: datetime | None
    # Akun yang login di tablet; dipakai sebagai pilihan bawaan.
    is_login: bool


def _name(user: User) -> str:
    return user.name or user.username


def role_ids_of(db: Session, outlet_id: str, station_id: str) -> list[str]:
    """Peran yang mengerjakan stasiun di cabang ini: milik cabang bila diatur, selain itu peran bawaan stasiun."""
    own = list(
        db.scalars(
            select(StationBranchRole.role_id)
            .where(StationBranchRole.outlet_id == outlet_id, StationBranchRole.station_id == station_id)
            .order_by(StationBranchRole.role_id)
        ).all()
    )
    if own:
        return own
    return list(db.scalars(select(StationRole.role_id).where(StationRole.station_id == station_id).order_by(StationRole.role_id)).all())


def candidates(db: Session, outlet_id: str, station_id: str, login_user_id: str) -> list[Worker]:
    """Akun login lebih dulu, lalu karyawan yang sudah absen masuk dan belum absen keluar di cabang ini dengan peran jadwal yang dibolehkan; dibatasi dan diurutkan dari server."""
    login = db.get(User, login_user_id)
    found: list[Worker] = []
    if login is not None:
        found.append(Worker(login.id, _name(login), None, None, True))
    allowed = role_ids_of(db, outlet_id, station_id)
    if not allowed:
        return found
    rows = db.execute(
        select(User, Role.name, Attendance.clock_in_at, Attendance.status)
        .join(Attendance, Attendance.user_id == User.id)
        .join(Schedule, Schedule.id == Attendance.schedule_id)
        .join(Role, Role.id == Schedule.role_id)
        .where(
            Attendance.outlet_id == outlet_id,
            Schedule.role_id.in_(allowed),
            Attendance.clock_in_at.is_not(None),
            Attendance.clock_out_at.is_(None),
            User.is_active.is_(True),
            User.deleted_at.is_(None),
            User.id != login_user_id,
        )
        .order_by(Attendance.clock_in_at, User.id)
        .limit(MAX_WORKERS)
    ).all()
    seen = {login_user_id}
    for user, role_name, clock_in_at, status in rows:
        if status not in PRESENT_STATUSES or user.id in seen:
            continue
        seen.add(user.id)
        found.append(Worker(user.id, _name(user), role_name, clock_in_at, False))
    return found


def resolve(db: Session, outlet_id: str, station_id: str, login_user_id: str, worker_id: str | None) -> str:
    """Pelaku yang dicatat: akun login bila tidak dipilih, selain itu hanya karyawan yang memenuhi syarat saat ini; server memeriksa ulang karena daftar di tablet bisa basi."""
    if not worker_id or worker_id == login_user_id:
        return login_user_id
    if worker_id not in {worker.user_id for worker in candidates(db, outlet_id, station_id, login_user_id)}:
        raise DomainError(NOT_ELIGIBLE, status=CONFLICT)
    return worker_id
