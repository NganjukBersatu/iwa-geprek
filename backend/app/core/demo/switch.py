"""Menyalakan dan mematikan mode demo untuk seluruh sistem.

Mulai: skema demo dibuat, tabelnya dibangun migrasi yang sama dengan data asli, snapshot dimuat, lalu perangkat terpasang dan sesi
yang sedang masuk disalin supaya tablet dan aplikasi karyawan tetap tersambung. Baru setelah semua siap, saklar dinyatakan aktif dan
setiap transaksi diarahkan ke skema demo. Keluar: skema demo dihapus utuh, sehingga data asli kembali dipakai tanpa sisa demo.
"""
import logging
import threading
from dataclasses import dataclass

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine import Connection

from app.core.demo import snapshot
from app.core.demo.state import DEMO_SCHEMA, READY, STATE_TABLE, read_stage, remember, state_engine
from app.core.settings import SERVICE_ROOT, settings
from app.models.device import REGISTERED

log = logging.getLogger(__name__)

IDLE = "idle"
PREPARING = "preparing"
LOADING = "loading"
LINKING = "linking"
FAILED = "failed"
RUNNING = frozenset({PREPARING, LOADING, LINKING})
VERSION_TABLE = "alembic_version_v2"
LEGACY_TABLES = frozenset({"alembic_version"})
# Kunci penasihat PostgreSQL yang menjaga hanya satu proses menyalakan atau mematikan demo pada satu waktu.
SWITCH_LOCK = 7_340_525
PREPARE_FAILED = "DEMO_PREPARE_FAILED"
DEMO_OWNER_USERNAME = "demo"
STOP_LOCK_TIMEOUT = "10s"
# Kode PostgreSQL untuk batas tunggu kunci yang terlampaui.
LOCK_NOT_AVAILABLE = "55P03"


@dataclass(frozen=True)
class Status:
    available: bool
    active: bool
    stage: str
    percent: int
    error_code: str | None


class CashierStillOpen(Exception):
    """Masih ada sesi kasir asli yang terbuka; demo tidak boleh menyerobot penjualan sungguhan."""


class DemoBusy(Exception):
    """Skema demo masih dipakai transaksi lain lebih lama dari batas tunggu kunci; tidak ada yang dihapus."""


class DemoUnavailable(Exception):
    """Tombol demo dimatikan, atau snapshot demo tidak ada."""


def available() -> bool:
    return settings.demo_enabled and snapshot.SNAPSHOT_PATH.is_file()


def status() -> Status:
    with state_engine().connect() as conn:
        stage, percent, error_code = read_stage(conn)
    return Status(available(), stage == READY, stage or IDLE, percent, error_code)


def head_revision() -> str:
    heads = ScriptDirectory.from_config(_alembic_config()).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"migrasi punya {len(heads)} ujung")
    return heads[0]


def _alembic_config() -> Config:
    return Config(str(SERVICE_ROOT / "alembic.ini"))


def _set_stage(stage: str, percent: int, error_code: str | None = None) -> None:
    with state_engine().begin() as conn:
        conn.execute(text(f"UPDATE {DEMO_SCHEMA}.{STATE_TABLE} SET stage = :stage, percent = :percent, error_code = :code"), {"stage": stage, "percent": percent, "code": error_code})


def _drop(conn: Connection) -> None:
    conn.execute(text(f'DROP SCHEMA IF EXISTS "{DEMO_SCHEMA}" CASCADE'))


def start() -> Status:
    """Mulai menyiapkan demo di latar dan langsung mengembalikan statusnya; aman ditekan berkali-kali."""
    if not available():
        raise DemoUnavailable
    with state_engine().begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SWITCH_LOCK})
        stage, _, _ = read_stage(conn)
        if stage == READY or stage in RUNNING:
            return status()
        open_sessions = conn.scalar(text("SELECT count(*) FROM public.cash_sessions WHERE status = 'OPEN'"))
        if open_sessions:
            raise CashierStillOpen
        _drop(conn)
        conn.execute(text(f'CREATE SCHEMA "{DEMO_SCHEMA}"'))
        conn.execute(
            text(
                f"CREATE TABLE {DEMO_SCHEMA}.{STATE_TABLE} (stage text NOT NULL, percent integer NOT NULL, error_code text, "
                "started_at timestamptz NOT NULL DEFAULT now())"
            )
        )
        conn.execute(text(f"INSERT INTO {DEMO_SCHEMA}.{STATE_TABLE} (stage, percent) VALUES (:stage, 0)"), {"stage": PREPARING})
    # Satu pekerjaan per penyiapan; bila prosesnya mati di tengah, clear_stale membersihkan sisanya saat proses berikutnya mulai.
    threading.Thread(target=_prepare, name="demo-prepare", daemon=True).start()
    return status()


def _prepare() -> None:
    try:
        document = snapshot.read()
        config = _alembic_config()
        with state_engine().begin() as conn:
            conn.execute(text(f'SET LOCAL search_path TO "{DEMO_SCHEMA}"'))
            config.attributes["connection"] = conn
            config.attributes["version_table_schema"] = DEMO_SCHEMA
            config.attributes["keep_logging"] = True
            command.upgrade(config, "head")
            _ensure_complete(conn)
        _set_stage(LOADING, 0)
        with state_engine().begin() as conn:
            conn.execute(text(f'SET LOCAL search_path TO "{DEMO_SCHEMA}", public'))
            snapshot.load(conn, DEMO_SCHEMA, document, lambda percent: _set_stage(LOADING, percent))
        _set_stage(LINKING, 100)
        with state_engine().begin() as conn:
            conn.execute(text(f'SET LOCAL search_path TO "{DEMO_SCHEMA}", public'))
            _carry_over(conn)
        _set_stage(READY, 100)
        remember(True)
        log.info("demo mode on")
    except Exception:  # noqa: BLE001 - titik akhir pekerjaan latar: kegagalan apa pun dicatat dan dilaporkan lewat status, tidak ditelan.
        log.exception("demo preparation failed")
        try:
            _set_stage(FAILED, 0, PREPARE_FAILED)
        except Exception:  # noqa: BLE001 - status gagal tidak bisa ditulis; clear_stale membersihkan skema saat mulai berikutnya.
            log.exception("could not record the failed demo preparation")


def _ensure_complete(conn: Connection) -> None:
    """Setiap tabel data asli harus ada juga di skema demo, karena tabel yang hilang di sana akan terbaca dari data asli."""
    listed = text("SELECT tablename FROM pg_tables WHERE schemaname = :schema")
    missing = set(conn.scalars(listed, {"schema": "public"})) - set(conn.scalars(listed, {"schema": DEMO_SCHEMA})) - LEGACY_TABLES
    if missing:
        raise RuntimeError(f"tabel demo kurang: {', '.join(sorted(missing))}")


def _foreign_keys(conn: Connection, table: str) -> set[str]:
    return set(
        conn.scalars(
            text(
                "SELECT a.attname FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey) "
                "WHERE c.contype = 'f' AND c.conrelid = to_regclass(:table)"
            ),
            {"table": f"{DEMO_SCHEMA}.{table}"},
        )
    )


def _copy(conn: Connection, table: str, where: str, chosen: dict[str, str]) -> int:
    """Menyalin baris data asli ke demo; kolom kunci asing yang tidak dipilih dikosongkan karena barisnya tidak ada di demo."""
    columns = conn.scalars(
        text("SELECT column_name FROM information_schema.columns WHERE table_schema = :schema AND table_name = :table ORDER BY ordinal_position"),
        {"schema": DEMO_SCHEMA, "table": table},
    ).all()
    linked = _foreign_keys(conn, table)
    picked = [chosen.get(column, "NULL" if column in linked else f'"{column}"') for column in columns]
    names = ", ".join(f'"{column}"' for column in columns)
    copied = conn.execute(text(f'INSERT INTO "{DEMO_SCHEMA}"."{table}" ({names}) SELECT {", ".join(picked)} FROM public."{table}" WHERE {where} ON CONFLICT DO NOTHING'))
    return copied.rowcount


def _carry_over(conn: Connection) -> None:
    """Tablet terpasang dan akun yang sedang masuk ikut pindah ke demo, ditempatkan di cabang demo, supaya tidak ada yang perlu masuk ulang."""
    branch = conn.scalar(text(f'SELECT id FROM "{DEMO_SCHEMA}".outlets ORDER BY created_at, id LIMIT 1'))
    if branch is None:
        raise RuntimeError("snapshot demo tidak punya cabang")
    live = "id IN (SELECT user_id FROM public.login_sessions WHERE revoked_at IS NULL AND expires_at > now())"
    _copy(conn, "roles", "true", {})
    _copy(conn, "users", live, {"role_id": '"role_id"', "outlet_id": f"CASE WHEN outlet_id IS NULL THEN NULL ELSE '{branch}' END"})
    _copy(conn, "login_sessions", f'revoked_at IS NULL AND expires_at > now() AND user_id IN (SELECT id FROM "{DEMO_SCHEMA}".users)', {"user_id": '"user_id"'})
    _copy(conn, "devices", f"status = '{REGISTERED}'", {"outlet_id": f"'{branch}'"})
    # Stasiun dan printer tablet ikut, dicocokkan ke stasiun demo yang bernamanya sama, supaya tablet yang punya printer tetap mencetak.
    station = (
        f'(SELECT d.id FROM "{DEMO_SCHEMA}".stations d JOIN public.stations p ON lower(p.name) = lower(d.name) '
        "WHERE p.id = {table}.station_id ORDER BY d.position, d.id LIMIT 1)"
    )
    copied = f'device_id IN (SELECT id FROM "{DEMO_SCHEMA}".devices)'
    for table in ("device_stations", "device_station_prints"):
        _copy(conn, table, f"{copied} AND {station.format(table=table)} IS NOT NULL", {"device_id": '"device_id"', "station_id": station.format(table=table)})
    _copy(conn, "device_printers", copied, {"device_id": '"device_id"', "station_id": station.format(table="device_printers")})


def demo_owner_id(conn: Connection) -> str | None:
    return conn.scalar(text(f'SELECT id FROM "{DEMO_SCHEMA}".users WHERE username = :username AND deleted_at IS NULL'), {"username": DEMO_OWNER_USERNAME})


def stop() -> None:
    try:
        with state_engine().begin() as conn:
            # Permintaan lain hanya memegang kunci sebentar; menunggu tanpa batas akan menahan tombol keluar selamanya.
            conn.execute(text(f"SET LOCAL lock_timeout = '{STOP_LOCK_TIMEOUT}'"))
            conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SWITCH_LOCK})
            _drop(conn)
    except OperationalError as error:
        if getattr(error.orig, "sqlstate", None) != LOCK_NOT_AVAILABLE:
            raise
        raise DemoBusy from error
    remember(False)
    log.info("demo mode off")


def clear_stale() -> None:
    """Saat proses mulai: demo yang terputus di tengah penyiapan, gagal, atau tertinggal migrasi dihapus, karena tabelnya bisa tidak lengkap."""
    with state_engine().begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SWITCH_LOCK})
        stage, _, _ = read_stage(conn)
        if stage is None:
            if conn.scalar(text("SELECT to_regnamespace(:schema)"), {"schema": DEMO_SCHEMA}) is not None:
                _drop(conn)
            return
        revision = None
        if conn.scalar(text("SELECT to_regclass(:name)"), {"name": f"{DEMO_SCHEMA}.{VERSION_TABLE}"}) is not None:
            revision = conn.scalar(text(f"SELECT version_num FROM {DEMO_SCHEMA}.{VERSION_TABLE}"))
        if stage != READY or revision != head_revision():
            _drop(conn)
            log.warning("stale demo removed: stage=%s revision=%s", stage, revision)
