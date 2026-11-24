/** The sentences of the margin report of the menus. */
export const marginText = {
	sold: 'Terjual',
	cost: 'Modal',
	profit: 'Laba',
	afterDiscount: 'Setelah potongan',
	priceAtTransaction: 'Harga tercatat saat transaksi',
	grossProfit: 'Laba kotor',
	revenueMinusCost: 'Omzet dikurangi modal',
	partialCostWarning: 'Laba di atas lebih besar dari yang sebenarnya. Catat harga beli saat barang masuk, atau menu itu memang racikan yang stoknya tidak dilacak.',
	noTransactions: 'Belum ada transaksi',
	noTransactionsHint: 'Margin dihitung dari transaksi yang terjual. Ubah rentang tanggal lewat Filter untuk melihat periode lain.',
	topMenusTitle: '10 menu penyumbang omzet terbesar',
	chartLegend: 'Titik terang = modal, titik gelap = omzet, garis di antaranya = laba. Jarak sempit pada omzet besar berarti ramai tapi tidak menguntungkan.',
	chartSummary: 'Grafik dumbbell: titik modal dan titik omzet untuk sepuluh menu teratas; jarak keduanya adalah laba. Angka lengkap seluruh menu ada di tabel di bawah.',
	allMenus: 'Semua menu',
	searchPlaceholder: 'Cari nama menu...',
	noMatch: 'Tidak ada menu yang cocok dengan pencarian.',
	partialCost: 'modal sebagian',
	footnote: 'Modal diambil dari harga yang tercatat saat transaksi terjadi, bukan harga beli hari ini, jadi laba bulan lalu tidak ikut berubah saat supplier menaikkan harga. Transaksi yang dibatalkan tidak ikut dihitung. Persentase dihitung terhadap omzet.',
	menusWithoutCost: '{count} menu belum punya harga modal',
	menusCaption: '{count}{total} menu · {period}'
} as const;
