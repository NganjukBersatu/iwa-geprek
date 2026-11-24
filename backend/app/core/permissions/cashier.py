from app.core.permissions.model import Group, Permission, Section

GROUP = Group("cashier", "Kasir", (
    Section("Transaksi", (
        Permission("order.buat", "Buat transaksi", "Mencatat pesanan dan menerima pembayaran."),
        Permission("transaksi.ubah", "Edit transaksi", "Mengoreksi isi, pembayaran, dan nama pada transaksi yang sudah tercatat, di sesi siapa pun. Cocok untuk penanggung jawab; kasir cukup \"Koreksi dan hapus sesi sendiri\"."),
        Permission("transaksi.hapus", "Hapus transaksi", "Membuang transaksi dari semua laporan secara permanen, di sesi siapa pun. Cocok untuk penanggung jawab; kasir cukup \"Koreksi dan hapus sesi sendiri\"."),
        Permission("order.void", "Batalkan transaksi", "Membatalkan transaksi salah input. Mengubah angka pendapatan sesi."),
        Permission("order.void_shift_tutup", "Batalkan transaksi di sesi yang sudah tutup", "Membatalkan atau mengajukan pembatalan pada transaksi dari sesi yang sudah ditutup. Mengubah angka sesi yang sudah ditandatangani."),
        Permission("order.void.setujui", "Setujui pengajuan pembatalan", "Menyetujui atau menolak pengajuan pembatalan dari papan Daftar Pesanan."),
        Permission("kelebihan.lihat", "Lihat kelebihan pembayaran", "Membuka halaman Kelebihan Pembayaran: pembayaran non-tunai yang masuk lebih besar dari total pesanan, lengkap dengan waktu, kasir, nominal, dan pesanannya. Hanya membaca."),
    )),
    Section("Sesi kas", (
        Permission("shift.buka", "Buka dan tutup sesi", "Memegang uang di laci kasir: modal awal, rekap, dan selisih saat tutup."),
        Permission("shift.lihat_semua", "Lihat sesi semua orang", "Tanpa ini hanya sesinya sendiri yang terlihat. Cocok untuk penanggung jawab yang mengawasi sesi kasir."),
        Permission("sesi.koreksi", "Koreksi sesi kas", "Mengubah modal awal, uang aktual, dan catatan sesi kas milik siapa pun, juga yang sudah ditutup. Cocok untuk penanggung jawab; kasir cukup \"Koreksi dan hapus sesi sendiri\"."),
        Permission("sesi.hapus", "Hapus sesi kas", "Membuang sesi kas milik siapa pun beserta seluruh transaksinya secara permanen. Cocok untuk penanggung jawab; kasir cukup \"Koreksi dan hapus sesi sendiri\"."),
        Permission("sesi.kelola_sendiri", "Koreksi dan hapus sesi sendiri (yang sedang berjalan)", "Cocok untuk kasir. Mengoreksi atau menghapus sesi kas berjalan yang ia pegang sendiri, beserta mengedit dan menghapus transaksi di dalamnya. Beda dengan \"Koreksi sesi kas\", \"Hapus sesi kas\", \"Edit transaksi\", dan \"Hapus transaksi\" yang berlaku untuk sesi siapa pun, juga yang sudah ditutup. Sesi yang sudah ditutup atau milik orang lain tetap tertutup baginya."),
        Permission("shift.lewati_gerbang", "Lewati gerbang buka sesi", "Menutup jendela Buka Sesi dengan \"Nanti saja\" tanpa membuka sesi."),
        Permission("checklist.tambah_baris", "Tambah baris Project dan Komplain saat tutup sesi", "Menambah lebih dari satu baris pada isian Project dan Komplain di checklist tutup sesi."),
    )),
    Section("Papan pesanan", (
        Permission("order.status", "Papan pesanan", "Mengerjakan item di papan stasiun: mulai, selesai, dan kembalikan."),
        Permission("stasiun.kelola", "Atur stasiun dan alur kerja", "Menambah stasiun, mengatur target waktu, menetapkan stasiun tiap kategori menu, pengaturan per cabang, dan menyalakan alur papan stasiun."),
        Permission("stasiun.intervensi", "Intervensi stasiun", "Memajukan atau mengembalikan item di stasiun dari web dengan alasan, misalnya saat tablet stasiun mati. Tercatat atas nama pemegangnya dan tidak dihitung ke kinerja karyawan."),
    )),
))
