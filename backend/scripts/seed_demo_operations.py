"""Data demo operasional dan karyawan: SOP, tugas outlet dan rutin beserta pengisiannya, tugas pribadi dan pemberitahuannya, izin, libur, lembur, barang rutin, stok opname, dan setoran.

    python scripts/seed_demo_operations.py           # menampilkan rencana dan menulis tidak apa pun
    python scripts/seed_demo_operations.py --tulis   # menulis data demo setelah Anda mengetik "ya"
    python scripts/seed_demo_operations.py --hapus   # menghapus data demo ini setelah Anda mengetik "ya"

Hanya untuk database pengembangan atau skema bangun snapshot (SEED_SCHEMA); ia menulis ke cabang pertama.
Butuh data dari seed_demo_sales, seed_demo_inventory, dan seed_demo_attendance, jadi jalankan setelah ketiganya, dan hapus data ini lebih dulu sebelum menghapus ketiganya.
Baris bertipe teks memakai id berawalan "demo-ops-"; tabel yang id-nya bertipe UUID memakai UUID tetap yang diturunkan dari nama, sehingga tetap bisa dihapus tepat.
Stok opname dan setoran ditulis lewat aturan aplikasi yang sama dengan layar web, jadi kartu reset stok dan batas setoran per hari ikut benar.
"""
import random
import sys
import uuid
from datetime import date, datetime, time, timedelta
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, inspect, select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import IntegrityError, ProgrammingError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core import money_trail  # noqa: E402
from app.core.clock import WIB, now  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.errors import DomainError  # noqa: E402
from app.core.finance import deposited  # noqa: E402
from app.core.ingredients import counts  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.employee.batches.constants import (  # noqa: E402
    KIND_NUMBER,
    KIND_TEXT,
    KIND_TOGGLE,
    TOGGLE_OK,
    TOGGLE_PROBLEM,
)
from app.employee.notices.constants import TASK_ASSIGNED, TASK_KIND, TASK_OVERDUE  # noqa: E402
from app.models.attendance import Attendance, AttendanceStatus  # noqa: E402
from app.models.day_off import DayOff  # noqa: E402
from app.models.deposit import Deposit, DepositDay  # noqa: E402
from app.models.ingredient import Ingredient, IngredientCount  # noqa: E402
from app.models.leave_request import LeaveRequest, LeaveStatus, LeaveType  # noqa: E402
from app.models.notice import Notice  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.outlet_batch import (  # noqa: E402
    FILL_EACH,
    FILL_ONE,
    KIND_OUTLET,
    KIND_ROUTINE,
    SHARED_FILLER,
    TARGET_SHIFT,
    UNIT_DAY,
    OutletBatch,
    OutletBatchAnswer,
    OutletBatchItem,
    OutletBatchRun,
    OutletBatchShiftCode,
)
from app.models.outlet_task import OutletTask  # noqa: E402
from app.models.overtime import Overtime  # noqa: E402
from app.models.routine_item import RoutineItem  # noqa: E402
from app.models.schedule import Schedule  # noqa: E402
from app.models.shift_code import ShiftCode  # noqa: E402
from app.models.sop import Sop, SopRead, SopSlide  # noqa: E402
from app.models.task import Task, TaskStatus, TaskType  # noqa: E402
from app.models.user import User  # noqa: E402
from web.management.deposits.domain import allocate  # noqa: E402
from web.management.deposits.service import due_by_day  # noqa: E402
from web.management.ingredient_counts import repository as count_repository  # noqa: E402
from web.management.ingredient_counts import service as count_service  # noqa: E402
from web.management.ingredient_counts.domain import CountDraft, CountLine  # noqa: E402
from web.management.reports.inventory.ingredient_stock import service as stock_report  # noqa: E402

PREFIX = "demo-ops-"
CONFIRMATION = "ya"
# Ruang nama tetap untuk UUID baris demo, supaya id yang sama bisa dihitung ulang saat menghapus.
UUID_SPACE = uuid.UUID("6f1d3c9e-0b7a-4f45-9a51-5d0e8c2b7a10")
HISTORY_DAYS = 7
DEPOSIT_DAYS = 10
COUNT_NOTE = "Penutupan periode data contoh"
# Selisih hitung fisik terhadap buku, sebagai bagian dari saldo buku.
COUNT_SHRINK = (Decimal(0), Decimal("0.03"))
QUANTITY = Decimal("0.001")
THOUSAND = Decimal(1000)
PARTIAL_SHARE = Decimal("0.6")

SOPS = (
    (
        "Membuka toko",
        (
            ("Sebelum buka", "Datang 30 menit sebelum jam buka, nyalakan lampu, dan periksa listrik serta gas."),
            ("Area pelanggan", "Pastikan meja, kursi, dan lantai bersih, lalu siapkan tisu dan alat makan."),
            ("Kasir", "Buka sesi kasir di tablet dan hitung uang di laci sesuai jumlah yang tercatat."),
        ),
    ),
    (
        "Kebersihan dapur",
        (
            ("Cuci tangan", "Cuci tangan dengan sabun sebelum mengolah bahan dan setiap kali berganti pekerjaan."),
            ("Penyimpanan bahan", "Simpan bahan mentah terpisah dari bahan matang, beri label tanggal, dan pakai yang lama lebih dulu."),
            ("Akhir shift", "Bersihkan kompor, meja kerja, dan peralatan, lalu buang sampah dan ganti kantong sampah."),
        ),
    ),
    (
        "Menutup kasir",
        (
            ("Pesanan terakhir", "Pastikan semua pesanan sudah dibayar dan tidak ada tagihan terbuka."),
            ("Hitung uang", "Hitung uang di laci, isi jumlahnya di tablet, dan laporkan selisih bila ada."),
            ("Tutup sesi", "Tutup sesi kasir, simpan uang di tempat yang ditentukan, lalu keluar dari tablet."),
        ),
    ),
)

OPENING_CHECK = (
    ("Lampu dan listrik menyala", KIND_TOGGLE),
    ("Area pelanggan bersih", KIND_TOGGLE),
    ("Suhu lemari pendingin (°C)", KIND_NUMBER),
    ("Catatan", KIND_TEXT),
)
SHIFT_CLEANING = (
    ("Meja kerja dibersihkan", KIND_TOGGLE),
    ("Peralatan dicuci dan dikeringkan", KIND_TOGGLE),
    ("Sampah dibuang", KIND_TOGGLE),
)

# (judul, keterangan, tenggat dari sekarang dalam jam, selesai)
TASKS = (
    ("Rapikan rak penyimpanan kering", "Susun ulang rak supaya bahan lama berada di depan.", -48, True),
    ("Periksa tanggal kedaluwarsa saus", "Catat saus yang kedaluwarsa dalam tujuh hari ke depan.", -24, True),
    ("Bersihkan filter penghisap asap", "Lepas filter, rendam dengan air sabun hangat, lalu pasang kembali.", -6, False),
    ("Foto kondisi area pelanggan", "Ambil foto area pelanggan setelah dirapikan untuk laporan mingguan.", 30, False),
)
OUTLET_TASKS = (
    ("Ganti lampu di area kasir", "Lampu di atas meja kasir redup; ganti dengan lampu cadangan di gudang.", -24, True),
    ("Isi ulang sabun cuci tangan", "Isi ulang semua tempat sabun di dapur dan toilet.", 8, False),
    ("Bersihkan kaca depan", "Lap kaca depan dari dalam dan luar sebelum jam ramai.", 20, False),
)
# (nama, siklus hari)
ROUTINE_ITEMS = (("Gas elpiji", 7), ("Sabun cuci piring", 14), ("Tisu", 10), ("Kantong sampah", 14))


def new_id() -> str:
    return f"{PREFIX}{uuid.uuid4()}"


def fixed_uuid(name: str) -> str:
    return str(uuid.uuid5(UUID_SPACE, f"{PREFIX}{name}"))


def task_ids() -> list[str]:
    return [fixed_uuid(f"task-{index}") for index in range(len(TASKS))]


def outlet_task_ids() -> list[str]:
    return [fixed_uuid(f"outlet-task-{index}") for index in range(len(OUTLET_TASKS))]


def notice_ids() -> list[str]:
    return [fixed_uuid(f"notice-{kind}-{index}") for index in range(len(TASKS)) for kind in (TASK_ASSIGNED, TASK_OVERDUE)]


def at_wib(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=WIB)


def whole_thousands(amount: Decimal) -> Decimal:
    return (amount / THOUSAND).to_integral_value(rounding=ROUND_FLOOR) * THOUSAND


PREFIXED_TABLES = (SopSlide, Sop, OutletBatch, LeaveRequest, DayOff, Overtime, RoutineItem, Deposit)
UUID_TABLES = ((Notice, notice_ids), (Task, task_ids), (OutletTask, outlet_task_ids))
ALL_MODELS = (
    Sop, SopSlide, SopRead, OutletBatch, OutletBatchItem, OutletBatchRun, OutletBatchAnswer, OutletBatchShiftCode,
    Task, Notice, OutletTask, LeaveRequest, DayOff, Overtime, RoutineItem, Deposit, DepositDay, IngredientCount,
)


def schema_mismatches(db: Session) -> list[str]:
    """Kolom model yang tidak ada di tabel database tujuan, supaya seed tidak menulis ke skema yang tertinggal migrasinya."""
    inspector = inspect(db.connection())
    problems = []
    for model in ALL_MODELS:
        table = model.__table__
        if not inspector.has_table(table.name):
            problems.append(f"tabel {table.name} tidak ada")
            continue
        present = {column["name"] for column in inspector.get_columns(table.name)}
        problems.extend(f"{table.name}.{column.name} tidak ada" for column in table.columns if column.name not in present)
    return problems


def demo_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Sop).where(Sop.id.like(f"{PREFIX}%"))) or 0


def demo_counts_of(db: Session, outlet_id: str) -> list[IngredientCount]:
    return list(db.scalars(select(IngredientCount).where(IngredientCount.outlet_id == outlet_id, IngredientCount.note == COUNT_NOTE)).all())


def delete_demo(db: Session, outlet: Outlet | None) -> None:
    if outlet is not None:
        for count in demo_counts_of(db, outlet.id):
            count_repository.delete_count(db, count)
    db.execute(delete(SopRead).where(SopRead.sop_id.like(f"{PREFIX}%")))
    for model, ids in UUID_TABLES:
        db.execute(delete(model).where(model.id.in_(ids())))
    # Item, pengisian, jawaban, kode shift tugas rutin, dan hari setoran ikut terhapus lewat foreign key CASCADE induknya.
    for model in PREFIXED_TABLES:
        db.execute(delete(model).where(model.id.like(f"{PREFIX}%")))
    db.commit()


def seed_sops(db: Session, owner: User, cashiers: list[User], stamp: datetime) -> int:
    for position, (title, slides) in enumerate(SOPS):
        sop = Sop(id=new_id(), title=title, active=True, sort_order=position, version=1, outlet_id=None, created_by_id=owner.id, updated_by_id=owner.id, created_at=stamp, updated_at=stamp)
        sop.slides = [SopSlide(id=new_id(), sop_id=sop.id, sort_order=order, title=slide_title, body=body) for order, (slide_title, body) in enumerate(slides)]
        db.add(sop)
        db.flush()
        if position == 0:
            for person in cashiers[:2]:
                db.add(SopRead(sop_id=sop.id, user_id=person.id, version=1, read_at=stamp + timedelta(hours=2)))
    return len(SOPS)


def new_batch(outlet: Outlet, name: str, kind: str, fill_mode: str, window: tuple[str, str], items: tuple[tuple[str, str], ...], first_day: date, position: int) -> OutletBatch:
    batch = OutletBatch(
        id=new_id(), outlet_id=outlet.id, kind=kind, fill_mode=fill_mode, target=TARGET_SHIFT, name=name, start_clock=window[0], end_clock=window[1],
        weekdays=None, repeat_unit=UNIT_DAY, repeat_every=1, starts_on=first_day, is_active=True, sort_order=position,
    )
    batch.items = [OutletBatchItem(id=new_id(), batch_id=batch.id, label=label, kind=kind_of, required=kind_of != KIND_TEXT, position=order) for order, (label, kind_of) in enumerate(items)]
    return batch


def answer_value(rng: random.Random, kind: str) -> str | None:
    if kind == KIND_TOGGLE:
        return TOGGLE_OK if rng.random() > 0.1 else TOGGLE_PROBLEM
    if kind == KIND_NUMBER:
        return str(rng.randint(2, 5))
    return None


def add_run(db: Session, rng: random.Random, batch: OutletBatch, day: date, filler_key: str, person: User, completed_at: datetime) -> None:
    run = OutletBatchRun(id=new_id(), batch_id=batch.id, day=day, filler_key=filler_key, completed_by_id=person.id, completed_at=completed_at)
    db.add(run)
    db.flush()
    for item in batch.items:
        db.add(OutletBatchAnswer(id=new_id(), run_id=run.id, item_id=item.id, item_label=item.label, item_kind=item.kind, value=answer_value(rng, item.kind)))


def present_shifts(db: Session, outlet: Outlet, first_day: date, today: date) -> list[tuple[Schedule, Attendance]]:
    """Jadwal demo yang benar-benar dihadiri di hari-hari lalu, karena hanya orang yang hadir yang bisa mengisi tugas."""
    rows = db.execute(
        select(Schedule, Attendance)
        .join(Attendance, Attendance.schedule_id == Schedule.id)
        .where(
            Schedule.outlet_id == outlet.id,
            Schedule.id.like("demo-att-%"),
            Schedule.date >= first_day,
            Schedule.date < today,
            Attendance.status.in_((AttendanceStatus.PRESENT, AttendanceStatus.LATE)),
        )
        .order_by(Schedule.date, Schedule.starts_at, Schedule.id)
    ).all()
    return [(schedule, attendance) for schedule, attendance in rows]


def seed_batches(db: Session, rng: random.Random, outlet: Outlet, codes: list[ShiftCode], shifts: list[tuple[Schedule, Attendance]], first_day: date) -> int:
    opening = new_batch(outlet, "Pemeriksaan buka toko", KIND_OUTLET, FILL_ONE, ("07:00", "10:00"), OPENING_CHECK, first_day, 0)
    cleaning = new_batch(outlet, "Kebersihan akhir shift", KIND_ROUTINE, FILL_EACH, ("14:00", "21:30"), SHIFT_CLEANING, first_day, 1)
    db.add_all((opening, cleaning))
    db.flush()
    for code in codes:
        db.add(OutletBatchShiftCode(batch_id=cleaning.id, shift_code_id=code.id))
    runs = 0
    opened_days: set[date] = set()
    for schedule, attendance in shifts:
        person = db.get(User, schedule.user_id)
        if person is None or attendance.clock_out_at is None:
            continue
        if schedule.date not in opened_days and attendance.clock_in_at is not None:
            opened_days.add(schedule.date)
            add_run(db, rng, opening, schedule.date, SHARED_FILLER, person, attendance.clock_in_at + timedelta(minutes=20))
            runs += 1
        add_run(db, rng, cleaning, schedule.date, person.id, person, attendance.clock_out_at - timedelta(minutes=10))
        runs += 1
    return runs


def seed_tasks(db: Session, outlet: Outlet, owner: User, cashiers: list[User], stamp: datetime) -> tuple[int, int]:
    notices = 0
    for index, ((title, description, due_hours, done), task_id) in enumerate(zip(TASKS, task_ids())):
        person = cashiers[index % len(cashiers)]
        due_at = stamp + timedelta(hours=due_hours)
        created_at = due_at - timedelta(days=2)
        db.add(
            Task(
                id=task_id, outlet_id=outlet.id, type=TaskType.ASSIGNMENT, status=TaskStatus.DONE if done else TaskStatus.OPEN, title=title, description=description,
                assignee_id=person.id, creator_id=owner.id, due_at=due_at, completion_note="Sudah dikerjakan." if done else None,
                completed_at=due_at - timedelta(hours=3) if done else None, created_at=created_at, updated_at=created_at,
            )
        )
        db.flush()
        db.add(Notice(id=fixed_uuid(f"notice-{TASK_ASSIGNED}-{index}"), user_id=person.id, kind=TASK_ASSIGNED, task_kind=TASK_KIND, task_id=task_id, title=title, show_at=created_at, read_at=created_at + timedelta(hours=1) if done else None, created_at=created_at))
        notices += 1
        if not done and due_at < stamp:
            db.add(Notice(id=fixed_uuid(f"notice-{TASK_OVERDUE}-{index}"), user_id=person.id, kind=TASK_OVERDUE, task_kind=TASK_KIND, task_id=task_id, title=title, show_at=due_at, created_at=due_at))
            notices += 1
    for index, ((title, description, due_hours, done), task_id) in enumerate(zip(OUTLET_TASKS, outlet_task_ids())):
        due_at = stamp + timedelta(hours=due_hours)
        created_at = due_at - timedelta(days=1)
        completer = cashiers[index % len(cashiers)] if done else None
        db.add(
            OutletTask(
                id=task_id, outlet_id=outlet.id, title=title, description=description, due_at=due_at, creator_id=owner.id,
                completer_id=completer.id if completer else None, completion_note="Selesai." if done else None,
                completed_at=due_at - timedelta(hours=2) if done else None, created_at=created_at, updated_at=created_at,
            )
        )
    return len(TASKS) + len(OUTLET_TASKS), notices


def seed_people(db: Session, rng: random.Random, outlet: Outlet, owner: User, cashiers: list[User], shifts: list[tuple[Schedule, Attendance]], first_day: date, today: date, stamp: datetime) -> tuple[int, int, int]:
    """Izin dan sakit mengikuti hari yang tercatat izin atau sakit di kehadiran demo, supaya kedua halaman saling cocok."""
    leaves = 0
    absent = db.scalars(
        select(Attendance)
        .where(Attendance.outlet_id == outlet.id, Attendance.id.like("demo-att-%"), Attendance.status.in_((AttendanceStatus.PERMIT, AttendanceStatus.SICK)))
        .order_by(Attendance.date.desc(), Attendance.id)
        .limit(3)
    ).all()
    for record in absent:
        sick = record.status is AttendanceStatus.SICK
        db.add(
            LeaveRequest(
                id=new_id(), outlet_id=outlet.id, user_id=record.user_id, type=LeaveType.SICK if sick else LeaveType.PERMIT, start_date=record.date, end_date=record.date,
                reason="Demam, istirahat sesuai saran dokter." if sick else "Keperluan keluarga.", status=LeaveStatus.APPROVED, decided_by_id=owner.id,
                decided_at=at_wib(record.date - timedelta(days=1), time(16, 0)), created_at=at_wib(record.date - timedelta(days=1), time(9, 0)),
            )
        )
        leaves += 1
    db.add(
        LeaveRequest(
            id=new_id(), outlet_id=outlet.id, user_id=cashiers[0].id, type=LeaveType.PERMIT, start_date=today + timedelta(days=3), end_date=today + timedelta(days=3),
            reason="Mengurus dokumen kependudukan.", status=LeaveStatus.PENDING, created_at=stamp - timedelta(hours=5),
        )
    )
    leaves += 1

    scheduled = set(db.execute(select(Schedule.user_id, Schedule.date).where(Schedule.outlet_id == outlet.id, Schedule.id.like("demo-att-%"))).all())
    day_offs = 0
    for person in cashiers:
        for offset in range(HISTORY_DAYS):
            day = first_day + timedelta(days=offset)
            if (person.id, day) not in scheduled:
                db.add(DayOff(id=new_id(), outlet_id=outlet.id, date=day, user_id=person.id, shift_code_id=None, note="Libur mingguan"))
                day_offs += 1
                break

    overtime = 0
    for schedule, attendance in rng.sample(shifts, min(3, len(shifts))):
        if attendance.clock_out_at is None:
            continue
        start_at = attendance.clock_out_at
        db.add(Overtime(id=new_id(), outlet_id=outlet.id, user_id=schedule.user_id, date=schedule.date, start_at=start_at, end_at=start_at + timedelta(minutes=rng.choice((60, 90, 120))), note="Membantu persiapan stok akhir pekan.", created_at=start_at, updated_at=start_at))
        overtime += 1
    return leaves, day_offs, overtime


def seed_routine_items(db: Session) -> int:
    for name, cycle in ROUTINE_ITEMS:
        # Tanggal beli berikutnya dihitung aplikasi dari pengeluaran yang menautkan barang ini; data contoh belum punya pengeluaran itu.
        db.add(RoutineItem(id=new_id(), name=name, cycle_days=cycle, last_purchased_at=None, next_due_date=None))
    return len(ROUTINE_ITEMS)


def seed_deposits(db: Session, outlet: Outlet, owner: User, today: date, stamp: datetime) -> int:
    """Setoran dibagi ke hari pendapatan lewat aturan yang sama dengan layar Setoran, dan yang terakhir sengaja belum lunas."""
    start, end = today - timedelta(days=DEPOSIT_DAYS), today - timedelta(days=1)
    due, paid = due_by_day(db, outlet.id, start, end), deposited.paid_by_day(db, outlet.id, start, end)
    open_days = [(day, due[day] - paid.get(day, Decimal(0))) for day in sorted(due) if due[day] - paid.get(day, Decimal(0)) > 0]
    groups = [open_days[index:index + 2] for index in range(0, len(open_days), 2)]
    written = 0
    for position, group in enumerate(groups):
        room = sum((left for _, left in group), Decimal(0))
        amount = whole_thousands(room * PARTIAL_SHARE if position == len(groups) - 1 else room)
        if amount <= 0:
            continue
        shares = allocate(amount, group)
        deposit = Deposit(id=new_id(), outlet_id=outlet.id, deposit_date=min(max(shares) + timedelta(days=1), today), amount=amount, note="Setoran tunai ke pemilik", user_id=owner.id, created_at=stamp)
        deposit.days = [DepositDay(id=new_id(), deposit_id=deposit.id, day=day, amount=share) for day, share in shares.items()]
        db.add(deposit)
        written += 1
    return written


def seed_count(db: Session, rng: random.Random, outlet: Outlet, owner: User) -> str:
    """Satu penutupan periode lewat pintu yang sama dengan layar Stok Opname; hasil hitung fisik sedikit di bawah buku seperti di lapangan."""
    start, end = counts.closing_period(db, outlet.id)
    report = stock_report.stock_report(db, outlet.id, start, end)
    demo_ids = set(db.scalars(select(Ingredient.id).where(Ingredient.outlet_id == outlet.id, Ingredient.id.like("demo-%"))).all())
    lines = []
    for row in report.rows:
        if row.ingredient_id not in demo_ids:
            continue
        book = max(row.closing_stock, Decimal(0))
        shrink = Decimal(str(rng.uniform(float(COUNT_SHRINK[0]), float(COUNT_SHRINK[1]))))
        lines.append(CountLine(row.ingredient_id, (book * (1 - shrink)).quantize(QUANTITY, rounding=ROUND_FLOOR)))
    if not lines:
        raise DomainError("Tidak ada bahan demo untuk dihitung.")
    count_service.close(db, owner, outlet.id, CountDraft(start=start, end=end, note=COUNT_NOTE, lines=lines))
    return f"{start:%d/%m/%Y}–{end:%d/%m/%Y}, {len(lines)} bahan"


def main() -> int:
    args = sys.argv[1:]
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}" + (f" (skema {settings.seed_schema})" if settings.seed_schema else "")
    print(f"Database: {target}")

    with SessionLocal() as db:
        try:
            problems = schema_mismatches(db)
            existing = 0 if problems else demo_count(db)
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1
        if problems:
            print(f"Model dan tabel database tidak cocok: {'; '.join(problems)}. Jalankan migrasi terbaru. Tidak ada yang diubah.")
            return 1

        owner = db.scalar(select(User).where(User.role_id == "owner", User.deleted_at.is_(None), User.is_active).order_by(User.id).limit(1))
        outlet = db.scalar(select(Outlet).order_by(Outlet.created_at, Outlet.id).limit(1))

        if "--hapus" in args:
            print(f"Akan menghapus data demo operasional: {existing} SOP beserta tugas, pemberitahuan, izin, libur, lembur, barang rutin, setoran, dan stok opname demo.")
            if input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
                print("Dibatalkan. Tidak ada yang dihapus.")
                return 1
            if owner is not None:
                money_trail.act_as(db, owner.id)
            delete_demo(db, outlet)
            print("Selesai. Data demo operasional dihapus.")
            return 0

        cashiers = list(db.scalars(select(User).where(User.id.like("demo-%"), User.username.like("demo.kasir%"), User.deleted_at.is_(None)).order_by(User.username)).all())
        codes = list(db.scalars(select(ShiftCode).where(ShiftCode.id.like("demo-att-%")).order_by(ShiftCode.sort_order, ShiftCode.id)).all())
        if outlet is None or owner is None or not cashiers or not codes:
            print("Belum ada cabang, pemilik, kasir demo, atau kode shift demo. Jalankan dulu seed_demo_sales, seed_demo_inventory, dan seed_demo_attendance. Tidak ada yang diubah.")
            return 1
        if existing:
            print(f"Sudah ada {existing} SOP demo. Hapus dulu dengan: python scripts/seed_demo_operations.py --hapus. Tidak ada yang diubah.")
            return 1

        print(f"Cabang tujuan: {outlet.name}")
        print(
            f"Rencana: {len(SOPS)} SOP, 2 tugas berulang dengan pengisian {HISTORY_DAYS} hari terakhir, {len(TASKS)} tugas pribadi beserta pemberitahuannya, "
            f"{len(OUTLET_TASKS)} tugas outlet, izin dan sakit, libur, lembur, {len(ROUTINE_ITEMS)} barang rutin, setoran {DEPOSIT_DAYS} hari terakhir, dan satu stok opname."
        )
        if "--tulis" not in args:
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0
        if input(f'Ketik "{CONFIRMATION}" untuk menulis ke {target}: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        rng = random.Random(2026)
        stamp = now()
        today = stamp.astimezone(WIB).date()
        first_day = today - timedelta(days=HISTORY_DAYS)
        try:
            money_trail.act_as(db, owner.id)
            sops = seed_sops(db, owner, cashiers, stamp - timedelta(days=30))
            shifts = present_shifts(db, outlet, first_day, today)
            runs = seed_batches(db, rng, outlet, codes, shifts, first_day)
            tasks, notices = seed_tasks(db, outlet, owner, cashiers, stamp)
            leaves, day_offs, overtime = seed_people(db, rng, outlet, owner, cashiers, shifts, first_day, today, stamp)
            routine = seed_routine_items(db)
            deposits = seed_deposits(db, outlet, owner, today, stamp)
            db.commit()
        except (IntegrityError, DomainError) as error:
            db.rollback()
            reason = f"{error.orig.__class__.__name__}: {error.orig}" if isinstance(error, IntegrityError) else str(error)
            print(f"Gagal: {reason}. Tidak ada yang tersimpan.")
            return 1
        print(f"Tertulis: {sops} SOP, {runs} pengisian tugas berulang, {tasks} tugas, {notices} pemberitahuan, {leaves} izin dan sakit, {day_offs} libur, {overtime} lembur, {routine} barang rutin, {deposits} setoran.")

        # Penutupan periode menyimpan dirinya sendiri, jadi dijalankan terakhir dan kegagalannya tidak membatalkan data di atas.
        try:
            closed = seed_count(db, rng, outlet, owner)
        except DomainError as error:
            db.rollback()
            print(f"Stok opname dilewati: {error}. Data lain tetap tersimpan; hapus semuanya dengan --hapus bila perlu.")
            return 1
        print(f"Stok opname ditutup untuk periode {closed}.")
        print("Buka SOP Karyawan, Tugas, Jadwal dan Kehadiran, Stok Opname, dan Setoran di web.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
