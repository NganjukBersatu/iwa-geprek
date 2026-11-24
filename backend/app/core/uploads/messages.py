"""The one sentence an upload can be refused with: the file is not what the feature takes, or is broken."""
from app.core.uploads.file import KIND_DOCUMENT, KIND_PHOTO, KIND_VIDEO
from app.core.uploads.rule import UploadRule

UNREADABLE = "Berkas yang dipilih tidak dapat dibaca atau rusak."
SEND_ONLY = "Unggah {accepted}."

# What each kind of file can be sent as, in the order the sentence lists them.
_ACCEPTED = (
    (KIND_PHOTO, "foto (JPG, PNG, WebP, atau HEIC)"),
    (KIND_VIDEO, "video (MP4, MOV, atau WEBM)"),
    (KIND_DOCUMENT, "dokumen PDF"),
)


def _joined(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    if len(names) == 2:
        return f"{names[0]} atau {names[1]}"
    return f"{', '.join(names[:-1])}, atau {names[-1]}"


def unreadable(rule: UploadRule) -> str:
    """Says what the feature does take, so the person knows what to send instead; the feature adds what happens to their request."""
    accepted = _joined([words for kind, words in _ACCEPTED if kind in rule.kinds])
    parts = (UNREADABLE, SEND_ONLY.format(accepted=accepted) if accepted else "", rule.unreadable_note)
    return " ".join(part for part in parts if part)
