/** The sentences of the incoming goods: the list, one record, its form, and the bulk entry. */
export const ingredientReceiptText = {
	bulkTitle: 'Isi banyak barang masuk',
	bulkHint: 'Tiap baris menambah stok bahan. Tidak ada pencatatan uang di sini.',
	recorded: 'Barang masuk dicatat.',
	proofPhoto: 'Foto bukti',
	noProofPhoto: 'Belum ada foto bukti',
	receipt: 'Barang masuk',
	removeNote: 'Saldo bahan menyesuaikan. Pengeluaran yang pernah dicatat untuk bahan ini tidak ikut terhapus.',
	recordReceipt: 'Catat barang masuk',
	branchRequired: 'Pilih cabang tempat barang masuk.',
	ingredientRequired: 'Pilih bahan yang datang.',
	quantityInvalid: 'Jumlah harus lebih dari 0. Isi jumlah bahan yang datang.',
	formDescription: 'Bahan yang datang menambah stok. Uang belanja dicatat di Pengeluaran.',
	ingredientSectionDescription: 'Bahan dan jumlah yang datang.',
	proofDescription: 'Nota atau foto barang yang datang.',
	listTitle: 'Daftar barang masuk',
	listDescription: 'Bahan yang datang menambah stok. Buka satu catatan untuk mengubah atau menghapusnya; pembayarannya dicatat di Pengeluaran.',
	searchPlaceholder: 'Cari nama bahan atau catatan...',
	search: 'Cari barang masuk',
	openProofPhoto: 'Buka foto bukti {name}',
	proofOf: 'Bukti {name}',
	viewProof: 'Lihat bukti {name}'
} as const;
