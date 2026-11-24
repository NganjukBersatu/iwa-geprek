"""The one door for every uploaded photo, video and document.

A feature declares an UploadRule and calls receive (or check), store and discard; it never looks at
extensions, sizes, file contents or the storage itself. Photos in any format become JPEG (an iPhone's
HEIC included) and large ones are shrunk when stored, so people are never refused over size or format.
Nothing outside this package imports app.core.storage.
"""
from app.core.uploads.file import KIND_DOCUMENT, KIND_PHOTO, KIND_VIDEO, UploadedFile
from app.core.uploads.receive import check, receive, receive_all
from app.core.uploads.rule import UploadRule
from app.core.uploads.store import discard, read, store

__all__ = [
    "KIND_DOCUMENT",
    "KIND_PHOTO",
    "KIND_VIDEO",
    "UploadRule",
    "UploadedFile",
    "check",
    "discard",
    "read",
    "receive",
    "receive_all",
    "store",
]
