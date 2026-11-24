from app.core.permissions.model import Group, Permission, Section

GROUP = Group("expenses", "Pengeluaran", (
    Section("Pengeluaran", (
        Permission("pengeluaran.catat", "Catat pengeluaran", "Mencatat belanja harian beserta buktinya."),
        Permission("pengeluaran.ubah_sendiri", "Ubah dan hapus pengeluaran sendiri", "Mengoreksi atau menghapus pengeluaran yang ia catat sendiri, selama sesinya belum ditutup."),
        Permission("pengeluaran.ubah_semua", "Ubah dan hapus pengeluaran siapa pun", "Mengoreksi atau menghapus pengeluaran milik siapa pun, juga setelah sesi ditutup."),
        Permission("pengeluaran.lihat_semua", "Lihat pengeluaran semua orang", "Tanpa ini hanya catatannya sendiri yang terlihat."),
        Permission("pengeluaran.pilih_shift", "Pilih sesi tujuan pengeluaran", "Menempelkan pengeluaran ke sesi kasir lain. Tanpa ini pengeluaran selalu masuk sesi aktifnya sendiri."),
        Permission("item_rutin.kelola", "Kelola item rutin", "Menentukan barang apa yang rutin dibeli dan siklusnya."),
    )),
    Section("Setoran", (
        Permission("setoran.lihat", "Lihat setoran", "Melihat uang tunai yang sudah disetor dan yang masih dipegang di Ringkasan Keuangan, beserta riwayat setorannya."),
        Permission("setoran.kelola", "Catat dan batalkan setoran", "Mencatat setoran beserta foto notanya, mengganti foto nota, dan membatalkan setoran."),
    )),
    Section("Mutasi uang", (
        Permission("mutasi.lihat", "Lihat Mutasi uang", "Membuka halaman Mutasi: uang modal, uang belanja, dan uang omzet tiap sesi beserta selisihnya. Hanya baca."),
    )),
))
