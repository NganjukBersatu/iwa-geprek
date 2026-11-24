from app.core.auth import AnyOf

PERMISSION_VIEW = "stok.lihat"
PERMISSION_RECEIVE = "stok.masuk"
PERMISSION_ADJUST = "stok.penyesuaian"
PERMISSION_COUNT = "stok.opname"
PERMISSION_CLOSE_PERIOD = "stok.tutup_periode"
PERMISSION_CORRECT = "stok.koreksi"

# Whoever may write a stock entry must be able to pick the ingredient, and read back what was just written.
PICK_GATE = AnyOf((PERMISSION_VIEW, PERMISSION_RECEIVE, PERMISSION_ADJUST, PERMISSION_COUNT, PERMISSION_CLOSE_PERIOD))
# Yang mengisi stok awal atau mengajukan tutup periode perlu melihat perjalanan dan riwayat bahan yang diisinya.
# Foto nota ikut barang masuk, foto bukti rusak ikut penyesuaian.
PROOF_GATE = AnyOf((PERMISSION_RECEIVE, PERMISSION_ADJUST))
HISTORY_GATE = AnyOf((PERMISSION_VIEW, PERMISSION_RECEIVE, PERMISSION_ADJUST, PERMISSION_COUNT, PERMISSION_CLOSE_PERIOD))

MAX_NOTE_LENGTH = 255
MAX_SEARCH_LENGTH = 100
MAX_ID_LENGTH = 64
DEFAULT_PAGE_SIZE = 30
CONFLICT = 409
FROM_COUNT_WEB_ONLY = "Catatan dari penutupan periode hanya bisa diubah admin di web."
FROM_OPENING_CARD = "Ubah atau hapus stok awal dari kartu Stok awal."
MESSAGE_UNKNOWN_KIND = "Jenis catatan stok tidak dikenal. Muat ulang halaman ini."
MAX_PAGE_SIZE = 100

# The recent-entry lists: which card kinds each screen shows.
KIND_RECEIPT = "receipt"
KIND_WASTE = "waste"
KIND_TRIAL = "trial"
