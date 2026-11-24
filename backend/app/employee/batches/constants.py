from app.core.storage import folders

PERMISSION_VIEW = "tugas.lihat"
PERMISSION_MANAGE = "tugas.kelola"

KIND_TEXT = "text"
KIND_NUMBER = "number"
KIND_PHOTO = "photo"
KIND_TOGGLE = "toggle"

TOGGLE_OK = "ok"
TOGGLE_PROBLEM = "problem"
TOGGLE_VALUES = (TOGGLE_OK, TOGGLE_PROBLEM)

CLOCK_SEPARATOR = ":"
WEEKDAY_SEPARATOR = ","

MAX_TEXT_LENGTH = 2000

MEDIA_FOLDER = folders.BATCH_PHOTO
