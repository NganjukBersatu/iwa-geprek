"""Mengisi database pengembangan dengan cepat, atau mengosongkannya; hanya berjalan pada database di komputer ini.

    python scripts/dev_data.py isi              # akun pemilik uji (bila belum ada) dan semua data contoh
    python scripts/dev_data.py kosongkan        # menghapus isi semua tabel setelah Anda mengetik "ya"; strukturnya tetap
    python scripts/dev_data.py kosongkan --ya   # sama, tanpa bertanya

Kata sandi akun uji dibuat acak, ditampilkan sekali, dan hanya disimpan sebagai hash.
Database di luar komputer ini selalu ditolak, supaya perintah ini tidak pernah mengenai staging atau produksi.
"""
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.user import User  # noqa: E402
from scripts.create_owner import OWNER_ROLE_ID, write_owner  # noqa: E402

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
CONFIRMATION = "ya"
TEST_USERNAME = "pemilik"
TEST_NAME = "Pemilik Uji"
TEST_BRANCH = "Cabang Uji"
# Tabel versi migrasi menyimpan posisi skema, bukan data, jadi tidak ikut dikosongkan.
KEPT_TABLES = frozenset({"alembic_version", "alembic_version_v2"})
# Urutan mengikuti ketergantungan tiap skrip: penjualan dulu, lalu yang membaca kasir, menu, dan kategori demo.
SEEDS = ("seed_demo_sales", "seed_demo_stations", "seed_demo_inventory", "seed_demo_finance", "seed_demo_attendance")


def target() -> str:
    url = make_url(settings.database_url)
    if url.host not in LOCAL_HOSTS:
        raise SystemExit(f"Ditolak: database {url.host} bukan di komputer ini. Perintah ini hanya untuk database pengembangan lokal.")
    return f"{url.host}:{url.port}/{url.database}"


def fill() -> int:
    with SessionLocal() as db:
        owner = db.scalar(select(User).where(User.role_id == OWNER_ROLE_ID, User.deleted_at.is_(None)).limit(1))
        if owner is None:
            password = secrets.token_urlsafe(18)
            has_branch = db.scalar(select(Outlet.id).limit(1)) is not None
            write_owner(db, None if has_branch else TEST_BRANCH, TEST_NAME, TEST_USERNAME, password)
            db.commit()
            print(f"Akun pemilik uji dibuat. Username: {TEST_USERNAME}  Kata sandi: {password}")
            print("Kata sandi ini hanya ditampilkan sekali; catat sekarang.")
        else:
            print(f"Akun pemilik sudah ada ({owner.username}); tidak dibuat lagi.")
    for name in SEEDS:
        done = subprocess.run([sys.executable, str(ROOT / "scripts" / f"{name}.py"), "--tulis"], input=f"{CONFIRMATION}\n", text=True, cwd=ROOT, capture_output=True)
        last = (done.stdout.strip().splitlines() or [done.stderr.strip()[-200:]])[-1]
        print(f"{name}: {last}")
        # Skrip yang menolak karena datanya sudah ada tidak menulis apa pun ke stderr; hanya kegagalan sungguhan yang menghentikan pengisian.
        if done.returncode != 0 and done.stderr.strip():
            print(done.stderr.strip()[-600:])
            return done.returncode
    return 0


def clear(asked: bool) -> int:
    where = target()
    with SessionLocal() as db:
        names = [name for name in db.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")) if name not in KEPT_TABLES]
        if not names:
            print("Tidak ada tabel untuk dikosongkan.")
            return 0
        print(f"Akan mengosongkan {len(names)} tabel di database {where}. Semua isinya hilang dan tidak bisa dikembalikan.")
        if asked and input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang dihapus.")
            return 1
        # Nama tabel berasal dari katalog database, bukan dari masukan pengguna.
        db.execute(text("TRUNCATE TABLE " + ", ".join(f'"{name}"' for name in names) + " RESTART IDENTITY CASCADE"))
        db.commit()
    print(f"Selesai. {len(names)} tabel kosong; jalankan 'python scripts/dev_data.py isi' untuk mengisinya lagi.")
    return 0


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments or arguments[0] not in ("isi", "kosongkan"):
        raise SystemExit(__doc__)
    print(f"Database: {target()}")
    return fill() if arguments[0] == "isi" else clear(asked="--ya" not in arguments[1:])


if __name__ == "__main__":
    sys.exit(main())
