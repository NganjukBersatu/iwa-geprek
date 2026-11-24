"""Kalimat yang dilihat admin di pengaturan kategori shift, di satu tempat."""

NOT_FOUND = "Kategori shift tidak ditemukan."
IN_USE = "Kategori '{name}' masih dipakai {count} kode shift, jadi tidak bisa dihapus. Pindahkan atau hapus kodenya lebih dulu."
NAME_TAKEN = "Nama kategori '{name}' sudah dipakai. Pilih nama lain."
NAME_REQUIRED = "Nama kategori wajib diisi."
ALL_BRANCHES_ONLY = "Pengaturan kategori berlaku untuk semua cabang, jadi hanya admin lintas cabang yang bisa mengubahnya."
OFF_HAS_NO_WINDOW = "Kategori berjenis Libur tidak punya rentang jam mulai. Kosongkan rentangnya, atau ubah jenisnya menjadi Hari kerja."
WINDOW_UNPAIRED = "Isi jam mulai paling awal dan paling akhir sekaligus, atau kosongkan keduanya."
WINDOW_SAME_CLOCK = (
    "Jam mulai paling awal dan paling akhir tidak boleh sama. "
    "Untuk rentang yang melewati tengah malam, isi jam paling akhir lebih kecil, misalnya 19:00 sampai 03:00."
)
