"""Turns what the client sent into UploadedFile; the only refusal is a file that cannot be read as anything the feature takes."""
from pathlib import Path

from fastapi import UploadFile

from app.core.errors import DomainError
from app.core.uploads import messages
from app.core.uploads.file import UploadedFile
from app.core.uploads.formats import identify
from app.core.uploads.rule import UploadRule

BYTES_PER_MEGABYTE = 1024 * 1024
MEMORY_GUARD_MEGABYTES = 100


def check(filename: str | None, content: bytes, rule: UploadRule) -> UploadedFile:
    found = identify(Path(filename or "").suffix.lower(), content)
    if found is None or found.kind not in rule.kinds:
        raise DomainError(messages.unreadable(rule))
    return found


async def receive(upload: UploadFile | None, rule: UploadRule, *, required: bool = True) -> UploadedFile | None:
    """Reads at most the memory guard, which only stops an abusive request, never a phone's photo or video."""
    if upload is None or (not required and not upload.filename):
        return None
    content = await upload.read(MEMORY_GUARD_MEGABYTES * BYTES_PER_MEGABYTE)
    return check(upload.filename, content, rule)


async def receive_all(uploads: list[UploadFile], rule: UploadRule) -> list[UploadedFile]:
    """Entries without a file name are skipped, as an empty form field arrives."""
    received = [await receive(upload, rule, required=False) for upload in uploads]
    return [item for item in received if item is not None]
