from app.core.permissions.model import Group, Permission, Section

GROUP = Group("figures", "Angka", (
    Section("Dashboard", (
        Permission("laporan.ringkasan", "Lihat ringkasan penjualan", "Kartu Pelanggan, Menu Terlaris, dan Pengeluaran Terbesar di Dashboard."),
        Permission("laporan.tren", "Lihat pemasukan, pengeluaran, dan tren", "Kartu Pemasukan, Pengeluaran, Keuntungan, grafik tren, dan ringkasan per periode di Dashboard."),
        Permission("laporan.laba_rugi", "Lihat laba rugi", "Kartu laba rugi di Dashboard, termasuk harga pokok penjualan."),
        Permission("laporan.nilai_persediaan", "Lihat nilai persediaan", "Nilai stok bahan di dalam kartu Laba Rugi di Dashboard."),
        Permission("laporan.kasir", "Lihat kinerja kasir", "Kartu penjualan per kasir di Dashboard."),
        Permission("laporan.pelanggan", "Lihat rincian pelanggan", "Rincian pelanggan yang terbuka dari kartu Pelanggan di Dashboard."),
        Permission("laporan.perbandingan", "Lihat perbandingan periode", "Selisih angka Dashboard terhadap periode sebelumnya."),
        Permission("laporan.transaksi", "Lihat rincian transaksi dan sesi", "Rincian transaksi dan sesi kasir yang terbuka dari kartu Dashboard, beserta ekspor transaksinya."),
    )),
    Section("Laporan", (
        Permission("laporan.overview", "Lihat Ringkasan Keuangan", "Ringkasan uang harian: omzet, pengeluaran, dan selisihnya."),
        Permission("laporan.ramai_penjualan", "Lihat Waktu Teramai Penjualan", "Jam dan hari tersibuk berdasarkan penjualan."),
        Permission("laporan.ramai_produk", "Lihat Waktu Teramai Produk", "Jam dan hari tersibuk untuk tiap produk."),
        Permission("laporan.kategori", "Lihat Kategori dan Produk", "Penjualan per kategori dan per produk."),
        Permission("laporan.varian_ekstra", "Lihat Varian dan Ekstra", "Penjualan per varian dan ekstra."),
        Permission("laporan.promo", "Lihat Laporan Promo", "Pemakaian dan dampak promo."),
        Permission("laporan.batal", "Lihat Transaksi Batal", "Transaksi yang dibatalkan beserta alasannya."),
        Permission("laporan.pengunjung", "Lihat Pengunjung", "Jumlah dan jenis pengunjung."),
        Permission("laporan.stok_bahan", "Lihat Stok Bahan", "Saldo dan pergerakan stok bahan."),
        Permission("laporan.perputaran", "Lihat Perputaran Stok", "Seberapa cepat stok berputar."),
        Permission("laporan.kehadiran", "Lihat Kehadiran Karyawan", "Rekap kehadiran karyawan."),
        Permission("laporan.margin", "Lihat Margin per Menu", "Margin tiap menu terhadap harga pokoknya."),
        Permission("laporan.kinerja_stasiun", "Lihat Kinerja Stasiun", "Waktu pengerjaan dan ketepatan tiap stasiun."),
        Permission("laporan.validasi", "Pemeriksaan non-tunai (QC)", "QC adalah pencocokan nominal non-tunai per tanggal dengan catatan sistem. Hanya untuk audit; tidak mengubah angka laporan."),
    )),
))
