"""Every sentence shown to the admin on the attendance screens, in one place."""
from web.management.attendance.constants import MAX_RANGE_DAYS

RECORD_NOT_FOUND = "Catatan kehadiran tidak ditemukan"
USER_NOT_FOUND = "Karyawan tidak ditemukan"
NO_BRANCH = "'{username}' belum ditempatkan di cabang mana pun."
LEAVE_KEEPS_CLOCK_IN = (
    "'{username}' sudah absen datang. Status izin/sakit/alfa tidak boleh menimpa jam datangnya; "
    "hapus catatan absennya dulu kalau memang keliru."
)
PRESENT_NEEDS_CLOCK_IN = "Status hadir/telat harus punya jam masuk"
CLOCK_OUT_BEFORE_IN = "Jam pulang lebih awal dari jam masuk"
RANGE_BACKWARDS = "Tanggal akhir lebih awal dari tanggal awal"
RANGE_TOO_LONG = f"Rentang kehadiran maksimal {MAX_RANGE_DAYS} hari"
