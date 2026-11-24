"""Database engine, session, and declarative base owned by v2."""
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core import cache, money_trail, query_budget, search
from app.core.settings import settings

POOL_SIZE = 3
POOL_OVERFLOW = 2
# Skema data demo; satu-satunya tempat namanya ditulis.
DEMO_SCHEMA = "demo"


def connect_args(demo_mode: bool) -> dict[str, str]:
    """Dalam mode demo skema demo selalu dicari pertama; public hanya untuk ekstensi bersama (pg_trgm), dan demo_schema_problem memastikan semua tabel ada di demo."""
    return {"options": f"-c search_path={DEMO_SCHEMA},public"} if demo_mode else {}


def demo_schema_problem(head: str) -> str | None:
    """Alasan proses demo tidak boleh mulai, atau None; skema demo yang tertinggal migrasi akan membuat tabel yang belum ada terbaca dari data asli."""
    with engine.connect() as conn:
        schemas = conn.scalar(text("SELECT current_schemas(false)")) or []
        if not schemas or schemas[0] != DEMO_SCHEMA:
            return f"Skema {DEMO_SCHEMA} belum ada. Isi dulu dengan: python scripts/demo_data.py isi"
        revision = conn.scalar(text(f"SELECT to_regclass('{DEMO_SCHEMA}.alembic_version_v2')")) and conn.scalar(text(f"SELECT version_num FROM {DEMO_SCHEMA}.alembic_version_v2"))
    if revision != head:
        return f"Skema {DEMO_SCHEMA} berada di migrasi {revision or '(kosong)'}, sedangkan kode di {head}. Hapus lalu isi ulang: python scripts/demo_data.py hapus, lalu isi"
    return None


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=POOL_OVERFLOW,
    connect_args=connect_args(settings.demo_mode),
)
query_budget.install(engine)
search.install(engine)
cache.install(engine)
money_trail.install(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Maps tables of the shared database; v2 creates its own tables only through its alembic folder, never from this metadata."""


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
