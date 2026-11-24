from app.core.uploads import KIND_PHOTO, UploadRule
from web.management.payment_methods import messages

RULE = UploadRule(
    kinds=frozenset({KIND_PHOTO}),
    unreadable_note=messages.IMAGE_UNREADABLE_NOTE,
    not_saved=messages.IMAGE_NOT_SAVED,
)
