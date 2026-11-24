PERMISSION_MANAGE = "kodeshift.kelola"

# Category kind of shift codes in the shared category list.
CATEGORY_KIND = "kode_shift"

CLOCK_PATTERN = r"^(([01]\d|2[0-3]):[0-5]\d|24:00)$"
COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"
MAX_CODE_LENGTH = 20
DEFAULT_SORT_ORDER = 0

# Jenis kategori yang diatur admin; kategori tanpa jenis tidak memeriksa apa pun.
KIND_WORK = "work"
KIND_OFF = "off"
CODE_KIND_MISMATCH = "SHIFT_CATEGORY_KIND_MISMATCH"
CODE_CLOCK_MISMATCH = "SHIFT_CATEGORY_CLOCK_MISMATCH"

# Shift terpanjang yang diterima; shift yang lebih panjang hampir pasti salah ketik.
MAX_SHIFT_MINUTES = 16 * 60
PROBLEM_SAME = "same_clock"
PROBLEM_TOO_LONG = "too_long"
CODE_START_AT_24 = "SHIFT_START_AT_24"
CODE_SHIFT_SAME_CLOCK = "SHIFT_END_SAME_AS_START"
CODE_NEEDS_MIDNIGHT = "SHIFT_NEEDS_MIDNIGHT_CONFIRMATION"
CODE_MIDNIGHT_UNNEEDED = "SHIFT_MIDNIGHT_FLAG_UNNEEDED"
CODE_SHIFT_TOO_LONG = "SHIFT_TOO_LONG"
