from dataclasses import dataclass

KIND_PHOTO = "photo"
KIND_VIDEO = "video"
KIND_DOCUMENT = "document"


@dataclass(frozen=True)
class UploadedFile:
    """A file that passed its rule; [kind] says how it was judged and [extension] keeps the leading dot."""

    kind: str
    extension: str
    content: bytes
