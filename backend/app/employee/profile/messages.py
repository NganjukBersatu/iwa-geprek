"""Every sentence shown to the employee, in one place."""
from app.employee.profile.constants import OLDEST_BIRTH_YEAR

NAME_REQUIRED = "Nama wajib diisi."
INVALID_PHONE = "Nomor telepon tidak valid. Gunakan angka, misalnya 081234567890."
INVALID_EMAIL = "Alamat email tidak valid. Contoh penulisan: nama@contoh.com."
INVALID_BIRTH_DATE = f"Tanggal lahir tidak valid. Isi tanggal yang sudah lewat, tahun {OLDEST_BIRTH_YEAR} atau sesudahnya."
INVALID_GENDER = "Pilih jenis kelamin dari pilihan yang tersedia."

WRONG_PASSWORD = "Kata sandi lama salah. Periksa kembali, lalu coba lagi."
SAME_PASSWORD = "Kata sandi baru harus berbeda dari kata sandi lama. Gunakan kata sandi lain."

PHOTO_UNREADABLE_NOTE = "Ambil foto ulang."
PHOTO_NOT_SAVED = "Foto gagal disimpan. Coba lagi."
