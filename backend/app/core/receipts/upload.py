"""The receipt photo of an expense, the same on the tablet and the management web."""
from app.core.uploads import KIND_PHOTO, UploadRule

RULE = UploadRule(
    kinds=frozenset({KIND_PHOTO}),
    unreadable_note="Foto ulang notanya.",
    not_saved="Foto nota gagal disimpan. Coba lagi.",
)
