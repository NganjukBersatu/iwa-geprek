from app.core.auth import AnyOf
from web.management.cafe_settings.constants import PERMISSION_MANAGE as SETTINGS_MANAGE

PERMISSION_MANAGE = "cabang.kelola"
PERMISSION_REMOVE = "cabang.hapus"
# Halaman cabang memuat pengaturan struk, harga dan margin, serta aturan absensi, jadi pemegang izin pengaturan juga boleh membukanya; mengubah cabang tetap butuh cabang.kelola.
READ_GATE = AnyOf((PERMISSION_MANAGE, SETTINGS_MANAGE))

MAX_NAME_LENGTH = 120
MAX_CODE_LENGTH = 16
MAX_NUMBER_LENGTH = 8
MAX_URL_LENGTH = 500
MAX_LOCATION_ID_LENGTH = 255
MIN_RADIUS_METERS = 1
MAX_RADIUS_METERS = 5000
DEFAULT_RADIUS_METERS = 50
NOT_FOUND = 404
CONFLICT = 409
