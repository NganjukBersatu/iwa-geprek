"""Data demo jadwal dan kehadiran untuk melihat halaman Jadwal, Kode Shift, dan Daftar Absensi di web; semua barisnya berawalan "demo-att-" supaya bisa dihapus lagi.

    python scripts/seed_demo_attendance.py           # menampilkan rencana dan menulis tidak apa pun
    python scripts/seed_demo_attendance.py --tulis   # menulis data demo setelah Anda mengetik "ya"
    python scripts/seed_demo_attendance.py --hapus   # menghapus data demo ini setelah Anda mengetik "ya"

Hanya untuk database pengembangan: ia menulis ke cabang pertama, dan database tujuannya (DATABASE_URL) ditampilkan sebelum menulis.
Butuh kasir demo dari scripts/seed_demo_sales.py. Hapus data ini lebih dulu sebelum menjalankan seed_demo_sales.py --hapus.
"""
import random
import sys
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import IntegrityError, ProgrammingError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.clock import WIB, now  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.models.attendance import Attendance, AttendanceStatus  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.schedule import Schedule  # noqa: E402
from app.models.shift_code import ShiftCode  # noqa: E402
from app.models.user import User  # noqa: E402

PREFIX = "demo-att-"
CONFIRMATION = "ya"
DAYS = 14
WORK_CHANCE = 0.85
# (kode, jam mulai, jam selesai, warna)
CODES = (("P", time(7, 0), time(15, 0), "#2E7D32"), ("S", time(13, 0), time(21, 0), "#1565C0"))
STATUS_WEIGHTS = ((AttendanceStatus.PRESENT, 70), (AttendanceStatus.LATE, 15), (AttendanceStatus.PERMIT, 5), (AttendanceStatus.SICK, 5), (AttendanceStatus.ABSENT, 5))
DEMO_TABLES = (Attendance, Schedule, ShiftCode)


def new_id() -> str:
    return f"{PREFIX}{uuid.uuid4()}"


def at_wib(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=WIB)


def demo_count(db: Session, model) -> int:
    return db.scalar(select(func.count()).select_from(model).where(model.id.like(f"{PREFIX}%"))) or 0


def delete_demo(db: Session) -> None:
    for model in DEMO_TABLES:
        db.execute(delete(model).where(model.id.like(f"{PREFIX}%")))
    db.commit()


def minutes(start: time, end: time) -> int:
    return (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)


def seed_codes(db: Session, outlet: Outlet) -> list[tuple[ShiftCode, time, time]]:
    created = []
    for position, (code, start, end, color) in enumerate(CODES):
        row = ShiftCode(
            id=new_id(),
            outlet_id=outlet.id,
            master_id=new_id(),
            code=code,
            start_clock=start.strftime("%H:%M"),
            end_clock=end.strftime("%H:%M"),
            color=color,
            duration_minutes=minutes(start, end),
            is_day_off=False,
            sort_order=position,
        )
        db.add(row)
        created.append((row, start, end))
    return created


def pick_status(rng: random.Random) -> AttendanceStatus:
    statuses, weights = zip(*STATUS_WEIGHTS)
    return rng.choices(statuses, weights=weights)[0]


def seed_day(db: Session, rng: random.Random, outlet: Outlet, user: list[User], codes: list[tuple[ShiftCode, time, time]], day: date, today: date, index: int) -> tuple[int, int]:
    schedules = attendance = 0
    for person_index, person in enumerate(user):
        if rng.random() > WORK_CHANCE:
            continue
        code, start, end = codes[(index + person_index) % len(codes)]
        entry = Schedule(
            id=new_id(),
            outlet_id=outlet.id,
            date=day,
            user_id=person.id,
            shift_code_id=code.id,
            starts_at=at_wib(day, start),
            ends_at=at_wib(day, end),
            role_id=person.role_id,
            clock_in_used=day < today,
        )
        db.add(entry)
        # Tabel tidak menyatakan relasi, jadi urutan tulis tidak otomatis: jadwal harus ada lebih dulu daripada kehadiran yang menunjuknya.
        db.flush()
        schedules += 1
        if day >= today:
            continue
        status = pick_status(rng)
        present = status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE)
        late_by = rng.randint(10, 45) if status is AttendanceStatus.LATE else rng.randint(-10, 5)
        clock_in = at_wib(day, start) + timedelta(minutes=late_by) if present else None
        clock_out = at_wib(day, end) + timedelta(minutes=rng.randint(0, 20)) if present else None
        db.add(
            Attendance(
                id=new_id(),
                outlet_id=outlet.id,
                user_id=person.id,
                date=day,
                shift_code_id=code.id,
                schedule_id=entry.id,
                status=status,
                clock_in_at=clock_in,
                clock_out_at=clock_out,
                note="Data demo" if not present else None,
            )
        )
        attendance += 1
    return schedules, attendance


def main() -> int:
    args = sys.argv[1:]
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}"
    print(f"Database: {target}")

    with SessionLocal() as db:
        try:
            existing = demo_count(db, Schedule)
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1

        if "--hapus" in args:
            print(f"Akan menghapus data demo: {existing} jadwal beserta kehadiran dan kode shift demo.")
            if input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
                print("Dibatalkan. Tidak ada yang dihapus.")
                return 1
            delete_demo(db)
            print("Selesai. Data demo jadwal dan kehadiran dihapus.")
            return 0

        outlet = db.scalar(select(Outlet).order_by(Outlet.created_at, Outlet.id).limit(1))
        user = list(db.scalars(select(User).where(User.id.like("demo-%"), User.username.like("demo.kasir%"), User.deleted_at.is_(None)).order_by(User.username)).all())
        if outlet is None or not user:
            print("Belum ada cabang atau kasir demo. Jalankan dulu scripts/seed_demo_sales.py --tulis. Tidak ada yang diubah.")
            return 1
        if existing:
            print(f"Sudah ada {existing} jadwal demo. Hapus dulu dengan: python scripts/seed_demo_attendance.py --hapus. Tidak ada yang diubah.")
            return 1

        print(f"Cabang tujuan: {outlet.name}")
        print(f"Rencana: {DAYS} hari terakhir untuk {len(user)} kasir demo, {len(CODES)} kode shift demo, kehadiran hadir, telat, izin, sakit, dan alfa.")
        if "--tulis" not in args:
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0
        if input(f'Ketik "{CONFIRMATION}" untuk menulis ke {target}: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        rng = random.Random(2026)
        today = now().astimezone(WIB).date()
        first_day = today - timedelta(days=DAYS - 1)
        totals = [0, 0]
        try:
            codes = seed_codes(db, outlet)
            db.flush()
            for index in range(DAYS):
                created = seed_day(db, rng, outlet, user, codes, first_day + timedelta(days=index), today, index)
                totals[0] += created[0]
                totals[1] += created[1]
            db.commit()
        except IntegrityError as error:
            db.rollback()
            print(f"Gagal: data bertabrakan atau melanggar aturan database ({error.orig.__class__.__name__}: {error.orig}). Tidak ada yang tersimpan.")
            return 1
        print(f"Selesai. {len(CODES)} kode shift, {totals[0]} jadwal, {totals[1]} catatan kehadiran demo ditulis.")
        print("Buka Jadwal dan Kehadiran, Kode Shift, dan Daftar Absensi di web.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
