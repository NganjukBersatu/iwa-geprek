"""Why an ingredient was thrown away; one list, read by the web form and the tablet, never copied."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Cause:
    code: str
    label: str
    human_error: bool


OTHER = "lainnya"

CAUSES = (
    Cause("kedaluwarsa", "Kedaluwarsa", False),
    Cause("busuk", "Busuk / basi sendiri", False),
    Cause("bencana", "Bencana (banjir, kebakaran)", False),
    Cause("hama", "Hama (tikus, serangga)", False),
    Cause("listrik", "Listrik padam / kulkas mati", False),
    Cause("tumpah", "Tumpah / jatuh", True),
    Cause("salah_olah", "Salah olah / gosong", True),
    Cause("lalai_simpan", "Lalai menyimpan", True),
    Cause("salah_takar", "Salah takar / kelebihan", True),
    Cause(OTHER, "Lainnya (tulis di catatan)", True),
)

BY_CODE = {cause.code: cause for cause in CAUSES}
HUMAN_ERROR_CODES = tuple(cause.code for cause in CAUSES if cause.human_error)
