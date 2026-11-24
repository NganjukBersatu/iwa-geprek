"""Database engine, session, and declarative base owned by v2."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core import cache, money_trail, query_budget, search
from app.core.settings import settings

POOL_SIZE = 3
POOL_OVERFLOW = 2


engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=POOL_SIZE, max_overflow=POOL_OVERFLOW)
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
