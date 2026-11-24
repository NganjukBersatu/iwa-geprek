"""Save a file and confirm its size, wherever it is kept."""
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.storage import bucket
from app.core.storage.images import mime_type, shrink
from app.models.stored_file import StoredFile

log = logging.getLogger(__name__)


class StorageError(Exception):
    """The file could not be put in the bucket; there is no silent fallback to the database."""


def save(db: Session, path: str, content: bytes, extension: str) -> None:
    """Does not commit; the caller owns the transaction."""
    content = shrink(content, extension)
    content_type = mime_type(extension)

    if bucket.is_active():
        try:
            bucket.put(path, content, content_type)
        except Exception as error:  # noqa: BLE001
            log.exception("Could not put %s in the bucket", path)
            raise StorageError(path) from error
        old = db.get(StoredFile, path)
        if old is not None:
            db.delete(old)
        return

    stored = db.get(StoredFile, path)
    if stored is None:
        db.add(StoredFile(path=path, content_type=content_type, content=content))
    else:
        stored.content_type = content_type
        stored.content = content


def save_confirmed(db: Session, path: str, content: bytes, extension: str) -> None:
    """Saves the file and checks that it really landed; does not commit."""
    save(db, path, content, extension)
    db.flush()
    if not size_of(db, path):
        raise StorageError(path)


def delete(db: Session, path: str | None) -> None:
    """Call after the row that owned the file is committed; a bucket failure leaves an orphan, never a broken row."""
    if not path:
        return
    stored = db.get(StoredFile, path)
    if stored is not None:
        db.delete(stored)
        db.commit()
    if bucket.is_active():
        try:
            bucket.delete(path)
        except Exception:  # noqa: BLE001
            log.warning("Could not delete %s from the bucket", path, exc_info=True)


def read(db: Session, path: str) -> tuple[bytes, str] | None:
    """The file's bytes and content type, from the bucket first and then the database."""
    if bucket.is_active():
        content = bucket.get(path)
        if content is not None:
            return content, mime_type(Path(path).suffix)
    stored = db.get(StoredFile, path)
    return (stored.content, stored.content_type) if stored is not None else None


def size_of(db: Session, path: str) -> int | None:
    if bucket.is_active():
        size = bucket.size_of(path)
        if size is not None:
            return size
    stored = db.get(StoredFile, path)
    return len(stored.content) if stored is not None else None
