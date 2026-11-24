from datetime import timedelta

PERMISSION_MANAGE = "kehadiran.kelola"

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
# Same as the schedule board: attendance is read by the week or month, two months are enough.
MAX_RANGE_DAYS = 62
DAYS_IN_WEEK = 7
MAX_NOTE_LENGTH = 300
NOT_FOUND = 404
# Absen yang diterima server lebih lama dari ini sesudah diambil di perangkat ditandai dikirim terlambat.
LATE_SUBMISSION_AFTER = timedelta(minutes=2)
