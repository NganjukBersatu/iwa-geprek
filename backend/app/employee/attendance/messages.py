"""Every sentence shown to the employee, in one place."""
from app.employee.attendance.constants import MAX_OFFLINE_AGE_HOURS
from app.employee.schedule.constants import CLOCK_IN_EARLY_MINUTES, SELF_SCHEDULE_RANGE_MINUTES

SCHEDULE_NOT_OPEN = (
    f"Jadwal ini tidak bisa diabsen sekarang. Absen datang dibuka {CLOCK_IN_EARLY_MINUTES} menit sebelum jam mulai "
    "sampai jam selesai, dan setiap jadwal hanya bisa diabsen sekali. Buka ulang halaman absen."
)
ALREADY_CLOCKED_IN ="Anda masih punya absen datang yang belum ditutup. Absen pulang dulu sebelum absen datang lagi."
NOT_CLOCKED_IN = "Tidak ada absen datang yang belum ditutup. Silakan absen datang terlebih dahulu."
AUTO_CLOSED = (
    "Absen datang Anda sudah ditutup otomatis oleh sistem karena tidak ada absen pulang sampai batas waktu "
    "setelah jam selesai shift. Buka ulang halaman absen untuk melihat rinciannya."
)

SELF_SCHEDULE_EXISTS = "Anda sedang libur atau masih dalam rentang jam jadwal lain, jadi tidak bisa membuat jadwal sendiri."
SELF_SCHEDULE_OVERLAP = "Rentang jam kode shift ini bertabrakan dengan jadwal Anda yang lain. Pilih dari saran yang tersedia."
SELF_SCHEDULE_OUT_OF_RANGE = (
    f"Jam mulai kode shift ini lebih dari {SELF_SCHEDULE_RANGE_MINUTES} menit dari sekarang. "
    "Pilih dari saran yang tersedia."
)
SELF_SCHEDULE_NOT_FOUND = "Cabang, peran, atau kode shift tidak ditemukan. Muat ulang pilihan."

INVALID_LOCATION ="Lokasi tidak valid. Absen tidak dicatat. Ambil foto ulang setelah lokasi terkunci."
INVALID_LOCATION_MODE = "Pilihan lokasi absen tidak valid. Muat ulang halaman, lalu coba lagi."
OUTSIDE_NOTE_REQUIRED = "Absen di luar lokasi wajib menyertakan catatan, misalnya dibantukan ke cabang lain. Isi catatannya, lalu kirim ulang."
OUTSIDE_RADIUS = (
    "Anda {distance} m dari lokasi, di luar batas {radius} m. "
    "Pilih \"Absen di luar lokasi\" dan isi catatan kalau memang sedang bertugas di tempat lain."
)

CAPTURE_NEEDS_KEY = "Absen yang dikirim terlambat harus menyertakan kunci pengiriman. Perbarui aplikasi, lalu coba lagi."
INVALID_CAPTURE_TIME = "Waktu absen yang dikirim aplikasi tidak valid. Perbarui aplikasi, lalu coba lagi."
INVALID_TIME_SOURCE = "Sumber waktu absen tidak valid. Perbarui aplikasi, lalu coba lagi."
CAPTURED_IN_FUTURE = "Waktu absen dari aplikasi lebih maju dari waktu server. Periksa tanggal dan jam di HP Anda, lalu kirim ulang."
CAPTURED_TOO_OLD = (
    f"Absen ini dibuat lebih dari {MAX_OFFLINE_AGE_HOURS} jam yang lalu, jadi tidak bisa dikirim lagi. "
    "Hubungi admin untuk mencatat absennya."
)
KEY_REUSED = "Kunci pengiriman ini sudah dipakai untuk absen yang berbeda. Buat absen baru, lalu kirim."

PHOTO_UNREADABLE_NOTE = "Absen tidak dicatat. Ambil foto ulang."
PHOTO_NOT_SAVED = "Foto gagal disimpan, jadi absen tidak dicatat. Coba absen lagi."
