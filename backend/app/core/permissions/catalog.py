from app.core.permissions.model import Group, Permission, Section

GROUP = Group("catalog", "Katalog", (
    Section("Menu", (
        Permission("menu.tersedia", "Tandai menu habis", "Menandai menu habis atau tersedia lagi dari layar kasir."),
        Permission("menu.kelola", "Kelola menu", "Menambah, mengubah harga, dan menghapus menu. Berlaku untuk semua cabang."),
        Permission("varian.kelola", "Kelola varian menu", "Membuat kelompok varian (pilihan yang tidak mengubah harga), memilih menu mana yang memakainya, dan menentukan bahan yang terpakai per pilihan."),
        Permission("ekstra.kelola", "Kelola ekstra menu", "Membuat ekstra (tambahan berharga), menentukan harga per cabang, menu mana yang boleh diberi ekstra, dan bahan yang terpakai."),
    )),
    Section("Resep", (
        Permission("resep", "Lihat resep (tanpa harga pokok)", "Membuka Master Resep hanya untuk lihat bahan dan takarannya, tanpa harga pokok, margin, atau angka biaya apa pun. Untuk karyawan yang ingin belajar resepnya."),
        Permission("resep.detail", "Lihat resep dan harga pokok penjualan (HPP)", "Membuka Master Resep: takaran bahan, harga pokok penjualan (HPP, yaitu biaya bahan untuk satu menu), dan margin tiap menu."),
        Permission("resep.kelola", "Kelola resep", "Menyimpan dan menghapus resep menu, termasuk menerapkannya ke semua cabang."),
    )),
    Section("Promo", (
        Permission("promo.kelola", "Kelola promo", "Menentukan diskon berarti menentukan pendapatan."),
    )),
    Section("Kategori dan satuan", (
        Permission("referensi.kelola", "Kelola kategori dan satuan", "Menambah, mengganti nama, dan menghapus daftar kategori dan satuan. Yang masih dipakai tidak bisa dihapus."),
    )),
))
