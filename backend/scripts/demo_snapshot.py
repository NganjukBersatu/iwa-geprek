"""Membuat snapshot data demo sekali dari scripts/demo_catalog.json milik klien: backend/demo/snapshot.json.gz, yang ikut deploy.

    python scripts/demo_snapshot.py

Aman dijalankan saat mode demo aktif: snapshot baru berlaku saat demo dimulai lagi. Data dibangun di skema sementara demo_build pada database ini (seed penjualan, stasiun, stok, keuangan, absensi), disimpan ke
snapshot, lalu skema itu dihapus lagi. Data asli tidak pernah ditulis. Jalankan ulang hanya bila katalog demo berubah; tombol
"Coba mode demo" di layar masuk web admin memuat snapshot ini dengan tanggal digeser ke hari ini.
"""
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import Connection, create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.demo import snapshot  # noqa: E402
from app.core.demo.switch import LEGACY_TABLES, head_revision  # noqa: E402
from app.core.settings import settings  # noqa: E402
from scripts import demo_catalog  # noqa: E402
from scripts.create_owner import write_owner  # noqa: E402
from scripts.dev_data import CONFIRMATION, SEEDS  # noqa: E402

BUILD_SCHEMA = "demo_build"
VERSION_TABLE = "alembic_version_v2"
DEMO_USERNAME = "demo"
DEMO_OWNER_NAME = "Pemilik Demo"
# Seed keuangan menunggu sesi kas yang sedang terbuka, yang tidak ada saat membangun snapshot; boleh dilewati.
OPTIONAL_SEEDS = frozenset({"seed_demo_finance"})


class BuildRefused(Exception):
    """Pembangunan ditolak sebelum menulis apa pun; pesannya untuk orang yang menjalankan perintah."""


def _locked(conn: Connection) -> None:
    """Koneksi bangun hanya boleh melihat skema bangun, supaya tabel yang belum dibuat gagal di sini, bukan menulis ke data asli."""
    conn.execute(text(f'SET LOCAL search_path TO "{BUILD_SCHEMA}"'))
    if conn.scalar(text("SELECT current_schemas(false)")) != [BUILD_SCHEMA]:
        raise BuildRefused("Ditolak: koneksi bangun masih melihat skema lain, jadi tidak ada yang ditulis.")


def _complete(conn: Connection) -> None:
    listed = text("SELECT tablename FROM pg_tables WHERE schemaname = :schema")
    missing = set(conn.scalars(listed, {"schema": "public"})) - set(conn.scalars(listed, {"schema": BUILD_SCHEMA})) - LEGACY_TABLES
    if missing:
        raise BuildRefused(f"Ditolak: {len(missing)} tabel belum ada di skema bangun ({', '.join(sorted(missing)[:5])}).")


def build() -> int:
    catalog = demo_catalog.load()
    head = head_revision()
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        real = conn.scalar(text(f"SELECT version_num FROM public.{VERSION_TABLE}")) if conn.scalar(text("SELECT to_regclass(:name)"), {"name": f"public.{VERSION_TABLE}"}) else None
    if real != head:
        raise BuildRefused("Data asli belum berada di migrasi terbaru. Jalankan dulu: python scripts/pra_deploy.py")

    print(f"Membangun data demo: cabang {catalog.branch_name}, {len(catalog.menus())} menu, {len(catalog.ingredients)} bahan.")
    with engine.begin() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{BUILD_SCHEMA}" CASCADE'))
        conn.execute(text(f'CREATE SCHEMA "{BUILD_SCHEMA}"'))
        _locked(conn)
        config = Config(str(ROOT / "alembic.ini"))
        config.attributes["connection"] = conn
        config.attributes["version_table_schema"] = BUILD_SCHEMA
        command.upgrade(config, "head")
        _complete(conn)
    try:
        with engine.begin() as conn:
            _locked(conn)
            with Session(bind=conn) as db:
                # Akun pemilik demo tidak pernah masuk dengan kata sandi (tombol demo yang memasukkannya), jadi kata sandinya acak dan dibuang.
                write_owner(db, catalog.branch_name, DEMO_OWNER_NAME, DEMO_USERNAME, secrets.token_urlsafe(24))
                db.flush()
        environment = {**os.environ, "SEED_SCHEMA": BUILD_SCHEMA}
        for name in SEEDS:
            done = subprocess.run([sys.executable, str(ROOT / "scripts" / f"{name}.py"), "--tulis"], input=f"{CONFIRMATION}\n", text=True, cwd=ROOT, capture_output=True, env=environment)
            last = (done.stdout.strip().splitlines() or [done.stderr.strip()[-200:]])[-1]
            print(f"{name}: {last}")
            # Snapshot hanya ditulis bila setiap seed wajib berhasil; snapshot setengah jadi akan menggantikan snapshot yang baik.
            if done.returncode != 0 and name not in OPTIONAL_SEEDS:
                print((done.stderr.strip() or done.stdout.strip())[-1500:])
                print("Snapshot tidak ditulis; snapshot sebelumnya tetap dipakai.")
                return done.returncode
        with engine.connect() as conn:
            counts = snapshot.export(conn, BUILD_SCHEMA, head)
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{BUILD_SCHEMA}" CASCADE'))
    size = snapshot.SNAPSHOT_PATH.stat().st_size // 1024
    print(f"Selesai. {sum(counts.values())} baris dari {len(counts)} tabel disimpan ke {snapshot.SNAPSHOT_PATH} ({size} KB).")
    print("Skema bangun sudah dihapus; data asli tidak berubah.")
    return 0


def main() -> int:
    try:
        return build()
    except (BuildRefused, demo_catalog.CatalogError, snapshot.SnapshotError) as refusal:
        print(refusal)
        return 1


if __name__ == "__main__":
    sys.exit(main())
