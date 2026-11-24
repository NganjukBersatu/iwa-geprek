"""Keeping and removing the files; the only place that talks to app.core.storage."""
from sqlalchemy.orm import Session

from app.core.errors import SERVICE_UNAVAILABLE, DomainError
from app.core.storage import files
from app.core.uploads.file import UploadedFile
from app.core.uploads.rule import UploadRule

# The code the web turns into its own sentence; it never changes meaning.
STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"

def store(db: Session, path: str, file: UploadedFile, rule: UploadRule) -> None:
    """Rolls the caller's whole change back when the file cannot be confirmed; does not commit."""
    try:
        files.save_confirmed(db, path, file.content, file.extension)
    except files.StorageError as error:
        db.rollback()
        raise DomainError(rule.not_saved, status=SERVICE_UNAVAILABLE, code=STORAGE_UNAVAILABLE) from error


def discard(db: Session, path: str | None) -> None:
    """Call after the row that owned the file is committed."""
    files.delete(db, path)


def read(db: Session, path: str) -> tuple[bytes, str] | None:
    return files.read(db, path)
