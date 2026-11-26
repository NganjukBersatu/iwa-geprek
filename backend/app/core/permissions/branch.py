from app.core.permissions.model import Group, Permission, Section

GROUP = Group("branch", "Cabang", (
    Section("Cabang", (
        Permission("cabang.kelola", "Kelola cabang", "Menambah cabang dan menutupnya."),
        Permission("cabang.hapus", "Hapus cabang permanen", "Menghapus cabang yang sudah tutup beserta seluruh datanya: order, sesi kasir, setoran, pengeluaran, stok, absen, dan fotonya. Tidak bisa dikembalikan; akun karyawannya dilepas dari cabang dan dinonaktifkan."),
        Permission("cabang.lintas", "Lihat dan pilih semua cabang", "Menampilkan pilihan cabang di sidebar dan membaca atau menulis data cabang mana pun yang dipilih, termasuk gabungan semua cabang. Tanpa izin ini, akun yang ditempatkan di satu cabang terkunci di cabangnya sendiri."),
    )),
    Section("Perangkat", (
        Permission("printer.uji", "Uji printer", "Mencetak struk percobaan dari printer yang tersambung. Tidak membaca dan tidak mengubah data apa pun."),
    )),
    Section("Pengaturan cabang", (
        Permission("pembayaran.kelola", "Atur cara pembayaran", "Menambah, mengubah, dan menghapus cara pembayaran; termasuk QRIS statis."),
        Permission("pengunjung.kelola", "Atur kategori pengunjung", "Menambah, mengubah, dan menghapus jenis rombongan (sendiri, berkeluarga, dan seterusnya) dan pilihan jenis kelamin yang muncul di kasir."),
        Permission("pengaturan.kelola", "Ubah pengaturan struk, harga, dan absensi", "Mengubah pengaturan struk, harga dan margin, serta aturan absensi cabang. Berikan dengan hati-hati: salah tangan di sini pernah mengubah WiFi dan identitas struk cabang tanpa sengaja."),
        Permission("panduan.lihat", "Panduan Setup", "Melihat daftar kesiapan cabang di dasbor: menu dan resep, metode bayar, karyawan kasir, dan perangkat kasir, beserta tautan untuk melengkapinya. Hanya membaca."),
    )),
))
