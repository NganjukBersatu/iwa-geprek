"""What a leave attachment must be."""
from app.core.uploads import KIND_DOCUMENT, KIND_PHOTO, UploadRule
from app.employee.leave import messages

RULE = UploadRule(
    kinds=frozenset({KIND_PHOTO, KIND_DOCUMENT}),
    unreadable_note=messages.ATTACHMENT_UNREADABLE_NOTE,
    not_saved=messages.ATTACHMENT_NOT_SAVED,
)
