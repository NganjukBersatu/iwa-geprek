from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core import live
from app.core.clock import now
from app.models.release_read import ReleaseRead, Surface

VERSION_PATTERN = r"^\d{1,4}\.\d{1,4}\.\d{1,4}$"
VERSION_MAX_LENGTH = 20


class ReleaseReadIn(BaseModel):
    version: str = Field(pattern=VERSION_PATTERN, max_length=VERSION_MAX_LENGTH)


class ReleaseReadOut(BaseModel):
    version: str
    read: bool


def state_of(db: Session, user_id: str, surface: Surface, version: str) -> ReleaseReadOut:
    read_version = db.scalar(select(ReleaseRead.version).where(ReleaseRead.user_id == user_id, ReleaseRead.surface == surface))
    return ReleaseReadOut(version=version, read=read_version == version)


def mark_read(db: Session, user_id: str, surface: Surface, version: str) -> ReleaseReadOut:
    # Penanda baca bukan perubahan data bisnis, jadi tidak memuat ulang layar mana pun.
    statement = insert(ReleaseRead).values(user_id=user_id, surface=surface, version=version, read_at=now())
    statement = statement.on_conflict_do_update(
        index_elements=[ReleaseRead.user_id, ReleaseRead.surface],
        set_={"version": statement.excluded.version, "read_at": statement.excluded.read_at},
    )
    db.execute(statement.execution_options(**live.SILENT))
    return ReleaseReadOut(version=version, read=True)
