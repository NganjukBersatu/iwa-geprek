"""Apakah mode demo sedang aktif, dan pengarah setiap transaksi ke skema demo selama aktif.

Statusnya tinggal di dalam skema demo itu sendiri (tabel demo_state), sehingga skema data asli tidak pernah ditambahi apa pun dan
semua jejak demo hilang saat skemanya dihapus. Status dibaca lewat mesin kecil tersendiri yang tidak ikut diarahkan, lalu disimpan
sebentar per proses supaya tidak menambah query di setiap permintaan.
"""
import threading
import time

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import Connection

from app.core.settings import settings

DEMO_SCHEMA = "demo"
STATE_TABLE = "demo_state"
READY = "ready"
# Proses lain (worker lain) melihat perubahan saklar paling lambat sebanyak ini.
RECHECK_SECONDS = 2.0
SEARCH_PATH = f"SET LOCAL search_path TO {DEMO_SCHEMA}, public"


class _Known:
    """Status terakhir yang dibaca proses ini; dijaga kunci karena dibaca dari banyak thread permintaan."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.active = False
        self.checked_at = float("-inf")
        self.engine: Engine | None = None


_known = _Known()


def state_engine() -> Engine:
    """Mesin kecil yang tidak pernah diarahkan ke skema demo; dipakai untuk membaca status dan untuk menyiapkan atau menghapus demo."""
    with _known.lock:
        if _known.engine is None:
            _known.engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=1, max_overflow=2)
        return _known.engine


def read_stage(conn: Connection) -> tuple[str | None, int, str | None]:
    """(tahap, persen, kode error) dari tabel status demo; tahap None berarti tidak ada demo sama sekali."""
    if conn.scalar(text("SELECT to_regclass(:name)"), {"name": f"{DEMO_SCHEMA}.{STATE_TABLE}"}) is None:
        return None, 0, None
    row = conn.execute(text(f"SELECT stage, percent, error_code FROM {DEMO_SCHEMA}.{STATE_TABLE} LIMIT 1")).first()
    return (row.stage, row.percent, row.error_code) if row is not None else (None, 0, None)


def is_active() -> bool:
    started = time.monotonic()
    with _known.lock:
        if started - _known.checked_at < RECHECK_SECONDS:
            return _known.active
    with state_engine().connect() as conn:
        stage, _, _ = read_stage(conn)
    with _known.lock:
        _known.active = stage == READY
        _known.checked_at = started
        return _known.active


def remember(active: bool) -> None:
    """Dipanggil proses yang baru saja menyalakan atau mematikan demo, supaya ia tidak menunggu pembacaan berikutnya."""
    with _known.lock:
        _known.active = active
        _known.checked_at = time.monotonic()


def install(engine: Engine) -> None:
    """Setiap transaksi di mesin aplikasi membaca skema demo lebih dulu selama demo aktif; public tetap terlihat untuk ekstensi pg_trgm."""
    # Proses seed pembangun snapshot sudah terkunci ke skema bangunnya sendiri dan tidak boleh ikut diarahkan.
    if settings.seed_schema:
        return

    @event.listens_for(engine, "begin")
    def _route(conn: Connection) -> None:
        if is_active():
            conn.exec_driver_sql(SEARCH_PATH)
