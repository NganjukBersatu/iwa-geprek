from app.core.uploads import KIND_PHOTO, UploadRule
from app.operational.menu import messages

RULE = UploadRule(
    kinds=frozenset({KIND_PHOTO}),
    unreadable_note=messages.PHOTO_UNREADABLE_NOTE,
    not_saved=messages.PHOTO_NOT_SAVED,
)
