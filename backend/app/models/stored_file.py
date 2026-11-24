from datetime import datetime, timezone

from sqlalchemy import DateTime, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

MAX_PATH_LENGTH = 500
MAX_CONTENT_TYPE_LENGTH = 100


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StoredFile(Base):
    """File content kept in the database; used when no bucket is configured and for old files."""

    __tablename__ = "stored_files"

    path: Mapped[str] = mapped_column(String(MAX_PATH_LENGTH), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(MAX_CONTENT_TYPE_LENGTH))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
