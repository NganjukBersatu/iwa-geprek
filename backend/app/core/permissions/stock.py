from app.core.permissions.model import Group, Permission, Section

GROUP = Group("stock", "Stok", (
    Section("Stok barang", (
        Permission("stok.lihat", "Lihat stok", "Melihat saldo dan riwayat mutasi barang."),
        Permission("stok.masuk", "Catat barang masuk", "Mencatat kiriman yang datang."),
        Permission("stok.penyesuaian", "Penyesuaian stok", "Mengubah saldo tanpa ada barang bergerak, misalnya barang rusak, tumpah, atau salah catat."),
        Permission("stok.opname", "Stok opname", "Mencocokkan saldo sistem dengan hitungan fisik; selisihnya tercatat."),
        Permission("stok.tutup_periode", "Ajukan tutup periode di tablet", "Menampilkan menu Stok Opname dan tombol Ajukan tutup periode di tablet. Admin yang menutup periodenya di web."),
        Permission("stok.atur", "Atur satuan dan batas stok", "Menentukan satuan, batas peringatan, dan menu mana yang dilacak stoknya."),
        Permission("stok.koreksi", "Koreksi dan hapus mutasi stok", "Mengedit atau menghapus baris riwayat stok dan bahan, mengubah isi periode opname yang sudah ditutup, dan membatalkan penutupannya."),
    )),
    Section("Bahan baku", (
        Permission("bahan.kelola", "Kelola bahan baku", "Menambah, mengubah, dan menghapus bahan beserta foto dan tautan katalognya."),
    )),
))
