from app.core.auth import AnyOf

PERMISSION_COUNT = "stok.opname"
PERMISSION_VIEW = "stok.lihat"
PERMISSION_CORRECT = "stok.koreksi"
# Sama dengan tombol Ajukan di tablet: mengajukan tutup periode, admin pemegang stok.opname yang menutup.
PERMISSION_REQUEST = "stok.tutup_periode"
# Lembar opname dibaca penutup dan pengaju; menulis hitungan dan menutup tetap hanya stok.opname.
SHEET_GATE = AnyOf((PERMISSION_COUNT, PERMISSION_REQUEST))

MAX_LINES = 500
CHANGES_PAGE_SIZE = 50
CHANGES_MAX_PAGE_SIZE = 100
DEFAULT_LIMIT = 50
MAX_LIMIT = 200
MAX_NOTE_LENGTH = 255
NOT_FOUND = 404
CONFLICT = 409
OPENING_LABEL = "Stok awal {day:%d/%m/%Y}"
