"""What a task's photos and videos must be."""
from app.core.uploads import KIND_PHOTO, KIND_VIDEO, UploadRule
from app.employee.tasks import messages

RULE = UploadRule(
    kinds=frozenset({KIND_PHOTO, KIND_VIDEO}),
    unreadable_note=messages.MEDIA_UNREADABLE_NOTE,
    not_saved=messages.MEDIA_NOT_SAVED,
)
