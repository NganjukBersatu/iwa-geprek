from app.core.auth import AnyOf

PERMISSION_VIEW = "stok.lihat"
PERMISSION_RECEIVE = "stok.masuk"
PERMISSION_ADJUST = "stok.penyesuaian"
PERMISSION_CORRECT = "stok.koreksi"
# A purchase note goes with receiving, waste or trial proof with adjusting.
PROOF_GATE = AnyOf((PERMISSION_RECEIVE, PERMISSION_ADJUST))

MAX_NOTE_LENGTH = 255
MAX_SEARCH_LENGTH = 100
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
NOT_FOUND = 404
