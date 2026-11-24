"""Photos and videos inside a procedure's slides: each lives in storage and is written into the text by its address."""
import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.http import SOP_FOLDER, sop_media_names
from app.core.uploads import UploadedFile
from app.models.sop import SopDraft
from web.management.sop.upload import RULE

FOLDER = SOP_FOLDER


def save(db: Session, file: UploadedFile) -> str:
    """Stored before any procedure refers to it, so the editor can show it at once; returns the file name."""
    name = f"{uuid.uuid4()}{file.extension}"
    uploads.store(db, f"{FOLDER}/{name}", file, RULE)
    db.commit()
    return name


def names_in(bodies: Iterable[str]) -> set[str]:
    return {name for body in bodies for name in sop_media_names(body)}


def discard_unused(db: Session, before: set[str], after: set[str]) -> None:
    """Files a save or a delete left without any slide, unless a draft still shows them; call after the change is committed."""
    drafted = names_in(db.scalars(select(SopDraft.content)).all())
    for name in before - after - drafted:
        uploads.discard(db, f"{FOLDER}/{name}")
