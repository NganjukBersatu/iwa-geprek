"""Data demo untuk presentasi: skema "demo" di database yang sama, terpisah penuh dari data asli.

    python scripts/demo_data.py isi          # membuat skema demo, tabelnya, akun pemilik demo, dan semua data contoh
    python scripts/demo_data.py hapus        # menghapus skema demo beserta seluruh isinya setelah Anda mengetik "ya"
    python scripts/demo_data.py hapus --ya   # sama, tanpa bertanya

Isinya diambil dari scripts/demo_catalog.json milik klien dan diisi sekali; untuk mengisi ulang, hapus dulu lalu isi lagi.
Untuk menampilkannya, jalankan backend dengan DEMO_MODE=true: proses itu hanya melihat skema demo. Tanpa DEMO_MODE, backend
melihat data asli dan tidak pernah membaca skema demo. Kata sandi akun demo dibuat acak, ditampilkan sekali, dan hanya disimpan
sebagai hash. Data asli tidak pernah ditulis: setiap langkah memeriksa bahwa koneksinya hanya melihat skema demo.
"""
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Harus sebelum modul app dimuat: mesin database lalu hanya membuka koneksi yang melihat skema demo.
os.environ["DEMO_MODE"] = "true"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from alembic.runtime.migration import MigrationContext  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402
from sqlalchemy import Connection, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.database import DEMO_SCHEMA, SessionLocal, engine  # noqa: E402
from app.core.settings import settings  # noqa: E402
from scripts import demo_catalog  # noqa: E402
from scripts.create_owner import write_owner  # noqa: E402
from scripts.dev_data import SEEDS  # noqa: E402

CONFIRMATION = "ya"
VERSION_TABLE = "alembic_version_v2"
# Tabel versi rantai migrasi lama yang hanya mungkin ada di data asli.
LEGACY_TABLES = frozenset({"alembic_version"})
DEMO_USERNAME = "demo"
DEMO_OWNER_NAME = "Pemilik Demo"


class DemoRefused(Exception):
    """Langkah demo ditolak sebelum menulis apa pun; pesannya untuk orang yang menjalankan perintah."""


def target() -> str:
    url = make_url(settings.database_url)
    return f"{url.host}:{url.port}/{url.database}, skema {DEMO_SCHEMA}"


def ensure_demo_only(conn: Connection) -> None:
    """Penjaga terakhir sebelum menulis: tabel baru dan setiap tabel yang ditulis harus jatuh ke skema demo, yang selalu dicari pertama."""
    schemas = conn.scalar(text("SELECT current_schemas(false)")) or []
    if DEMO_SCHEMA == "public" or not schemas or schemas[0] != DEMO_SCHEMA:
        raise DemoRefused("Ditolak: koneksi ini tidak terkunci ke skema demo, jadi tidak ada yang ditulis.")


def ensure_tables_in_demo(conn: Connection) -> None:
    """Sebelum menulis baris: setiap tabel data asli (sudah di migrasi terbaru) harus juga ada di skema demo, karena tabel yang hilang di sana akan jatuh ke public."""
    listed = text("SELECT tablename FROM pg_tables WHERE schemaname = :schema")
    missing = sorted(set(conn.scalars(listed, {"schema": "public"})) - set(conn.scalars(listed, {"schema": DEMO_SCHEMA})) - LEGACY_TABLES)
    if missing:
        raise DemoRefused(f"Ditolak: {len(missing)} tabel belum ada di skema demo ({', '.join(missing[:5])}), jadi tidak ada baris yang ditulis.")


def demo_tables(conn: Connection) -> int:
    return conn.scalar(text("SELECT count(*) FROM pg_tables WHERE schemaname = :schema"), {"schema": DEMO_SCHEMA}) or 0


def real_revision(conn: Connection) -> str | None:
    # Hanya membaca posisi migrasi data asli; skema demo dibuat dari kode yang sama, jadi tidak boleh lebih baru dari data asli.
    if conn.scalar(text("SELECT to_regclass(:name)"), {"name": f"public.{VERSION_TABLE}"}) is None:
        return None
    return conn.scalar(text(f"SELECT version_num FROM public.{VERSION_TABLE}"))


def create_tables(config: Config) -> None:
    with engine.begin() as conn:
        # Skema yang belum ada tidak terlihat di current_schemas, jadi penjaga baru bisa diperiksa setelah skemanya dibuat.
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DEMO_SCHEMA}"'))
        # Migrasi hanya melihat skema demo: tabel yang belum dibuat di demo gagal di sini, tidak pernah mengubah tabel asli di public.
        conn.execute(text(f'SET LOCAL search_path TO "{DEMO_SCHEMA}"'))
        if conn.scalar(text("SELECT current_schemas(false)")) != [DEMO_SCHEMA]:
            raise DemoRefused("Ditolak: koneksi migrasi demo masih melihat skema lain, jadi tidak ada yang dibuat.")
        config.attributes["connection"] = conn
        command.upgrade(config, "head")
        current = MigrationContext.configure(conn, opts={"version_table": VERSION_TABLE, "version_table_schema": DEMO_SCHEMA}).get_current_revision()
        ensure_tables_in_demo(conn)
        print(f"Tabel demo dibuat pada revisi {current}.")


def write_demo_owner(branch_name: str) -> str:
    password = secrets.token_urlsafe(18)
    with SessionLocal() as db:
        ensure_demo_only(db.connection())
        ensure_tables_in_demo(db.connection())
        write_owner(db, branch_name, DEMO_OWNER_NAME, DEMO_USERNAME, password)
        db.commit()
    return password


def run_seeds() -> int:
    environment = {**os.environ, "DEMO_MODE": "true"}
    for name in SEEDS:
        done = subprocess.run([sys.executable, str(ROOT / "scripts" / f"{name}.py"), "--tulis"], input=f"{CONFIRMATION}\n", text=True, cwd=ROOT, capture_output=True, env=environment)
        last = (done.stdout.strip().splitlines() or [done.stderr.strip()[-200:]])[-1]
        print(f"{name}: {last}")
        # Seed yang menolak karena syaratnya belum ada (misalnya sesi kas terbuka) tidak menulis ke stderr; hanya kegagalan sungguhan yang menghentikan pengisian.
        if done.returncode != 0 and done.stderr.strip():
            print(done.stderr.strip()[-600:])
            return done.returncode
    return 0


def fill() -> int:
    catalog = demo_catalog.load()
    config = Config(str(ROOT / "alembic.ini"))
    heads = ScriptDirectory.from_config(config).get_heads()
    with engine.connect() as conn:
        if demo_tables(conn):
            raise DemoRefused("Data demo sudah ada. Data demo diisi sekali; untuk mengisi ulang jalankan dulu: python scripts/demo_data.py hapus")
        if [real_revision(conn)] != heads:
            raise DemoRefused("Data asli belum berada di migrasi terbaru. Jalankan dulu: python scripts/pra_deploy.py")
    print(f"Mengisi data demo di {target()}: cabang {catalog.branch_name}, {len(catalog.menus())} menu, {len(catalog.ingredients)} bahan.")
    create_tables(config)
    password = write_demo_owner(catalog.branch_name)
    code = run_seeds()
    if code != 0:
        print("Pengisian berhenti. Hapus data demo yang setengah jadi dengan: python scripts/demo_data.py hapus --ya")
        return code
    print(f"Selesai. Akun pemilik demo: username {DEMO_USERNAME}, kata sandi {password}")
    print("Kata sandi ini hanya ditampilkan sekali; catat sekarang. Jalankan backend dengan DEMO_MODE=true untuk menampilkan data demo.")
    return 0


def remove(asked: bool) -> int:
    with engine.connect() as conn:
        count = demo_tables(conn)
    if count == 0:
        print("Tidak ada data demo. Tidak ada yang dihapus.")
        return 0
    print(f"Akan menghapus skema {DEMO_SCHEMA} di {target()}: {count} tabel demo beserta seluruh isinya. Data asli tidak tersentuh.")
    if asked and input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
        print("Dibatalkan. Tidak ada yang dihapus.")
        return 1
    with engine.begin() as conn:
        ensure_demo_only(conn)
        conn.execute(text(f'DROP SCHEMA "{DEMO_SCHEMA}" CASCADE'))
    print("Selesai. Semua data demo dihapus.")
    return 0


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments or arguments[0] not in ("isi", "hapus"):
        raise SystemExit(__doc__)
    try:
        return fill() if arguments[0] == "isi" else remove(asked="--ya" not in arguments[1:])
    except (DemoRefused, demo_catalog.CatalogError) as refusal:
        print(refusal)
        return 1


if __name__ == "__main__":
    sys.exit(main())
