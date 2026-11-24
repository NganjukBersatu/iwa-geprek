/** The sentences of the sales per order type and per branch, under the report of the busiest times of sales. */
export const salesBreakdownText = {
	orderType: 'Jenis',
	receipts: 'Struk',
	averagePerReceipt: 'Rata-rata per struk',
	grossProfit: 'Laba kotor',
	perOrderType: 'Per jenis pesanan',
	perOrderTypeCaption: '{period} · pesanan yang tidak dibatalkan',
	perBranch: 'Per cabang',
	perBranchCaption: '{period} · laba kotor dari subtotal item dikurangi harga pokok, kosong bila ada item tanpa harga pokok',
	noSales: 'Belum ada penjualan di periode ini.',
	loading: 'Memuat rincian penjualan',
	loadFailedTitle: 'Rincian penjualan belum tampil',
	loadFailed: 'Rincian penjualan belum bisa dimuat. Periksa koneksi, lalu coba lagi.'
} as const;
