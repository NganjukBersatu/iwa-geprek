from app.core.uploads import KIND_PHOTO, KIND_VIDEO, UploadRule
from web.management.sop import messages

RULE = UploadRule(
    kinds=frozenset({KIND_PHOTO, KIND_VIDEO}),
    unreadable_note=messages.MEDIA_UNREADABLE,
    not_saved=messages.MEDIA_NOT_SAVED,
)
