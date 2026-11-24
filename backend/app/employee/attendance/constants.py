from datetime import timedelta

from app.core import branch_settings
from app.core.storage import folders

PHOTO_FOLDER = folders.ATTENDANCE_PHOTO
CLOCK_OUT_PHOTO_SUFFIX = folders.CLOCK_OUT_PHOTO_SUFFIX

MAX_LATITUDE = 90
MAX_LONGITUDE = 180
MAX_ACCURACY_METERS = 100_000
MAX_NOTE_LENGTH = 500
MAX_NOTICE_IDS = 100
MAX_ID_LENGTH = 64

LOCATION_INSIDE = "inside"
LOCATION_OUTSIDE = "outside"
LOCATION_MODES = (LOCATION_INSIDE, LOCATION_OUTSIDE)

# The attendance table already stores these values in Indonesian.
STORED_LOCATION_MODE = {LOCATION_INSIDE: "dalam", LOCATION_OUTSIDE: "luar"}
LOCATION_MODE_FROM_STORED = {stored: mode for mode, stored in STORED_LOCATION_MODE.items()}

# Why a clock-in is not possible now; the app turns each into a sentence.
BLOCK_NOT_OPEN_YET = "not_open_yet"
BLOCK_ALREADY_USED = "already_used"
BLOCK_ENDED = "ended"
BLOCK_NO_SCHEDULE = "no_schedule"
BLOCK_NO_PERMISSION = "no_permission"

# Without it an employee cannot clock in or out, nor make a schedule for it; attendance is then marked by an admin.
PERMISSION_SELF_ATTENDANCE = "absensi.mandiri"

DEFAULT_LATE_TOLERANCE_MINUTES = branch_settings.DEFAULT_TOLERANCE_MINUTES
DEFAULT_LATE_PENALTY_PER_MINUTE = branch_settings.DEFAULT_PENALTY_PER_MINUTE
DEFAULT_AUTO_CLOSE_HOURS = branch_settings.DEFAULT_AUTO_CLOSE_HOURS

# Absen yang dikirim terlambat dari antrean app: sama dengan batas CHECK kolom idempotency_key di database.
MIN_IDEMPOTENCY_KEY_LENGTH = 8
MAX_IDEMPOTENCY_KEY_LENGTH = 64
# Selisih jam HP dan server yang masih dimaafkan, dan usia terlama absen yang masih diterima dari antrean.
CLOCK_SKEW = timedelta(minutes=2)
MAX_OFFLINE_AGE_HOURS = 24
MAX_OFFLINE_AGE = timedelta(hours=MAX_OFFLINE_AGE_HOURS)
