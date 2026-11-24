from dataclasses import dataclass

NOT_SAVED = "Berkas gagal disimpan. Coba lagi."


@dataclass(frozen=True)
class UploadRule:
    """What one feature takes: the kinds of file, and the words only the feature knows. Size and format are converted, never refused."""

    kinds: frozenset[str]
    unreadable_note: str = ""
    not_saved: str = NOT_SAVED
