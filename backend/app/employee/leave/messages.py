"""Every sentence shown to the employee, in one place."""
from app.employee.leave.constants import MAX_DAYS

END_BEFORE_START = "Tanggal selesai tidak boleh lebih awal dari tanggal mulai. Ubah salah satu tanggal."
TOO_LONG = f"Pengajuan maksimal {MAX_DAYS} hari. Persingkat rentang tanggalnya."
REASON_REQUIRED = "Alasan wajib diisi. Tuliskan alasan pengajuan Anda."
BAD_LINK = "Tautan harus diawali http:// atau https://. Periksa alamat tautan Anda."

ATTACHMENT_UNREADABLE_NOTE = "Pengajuan tidak dikirim."
ATTACHMENT_NOT_SAVED = "Lampiran gagal disimpan, jadi pengajuan tidak dikirim. Coba ajukan lagi."

NOT_FOUND = "Pengajuan tidak ditemukan. Muat ulang halaman untuk melihat daftar terbaru."
ALREADY_DECIDED = "Pengajuan yang sudah diputuskan tidak bisa dibatalkan. Muat ulang halaman untuk melihat statusnya."
