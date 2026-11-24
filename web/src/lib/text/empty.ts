/** Empty lists that offer a first step: what is missing, what to do next, and the label of the one button that does it. */
export const emptyText = {
	employees: { title: 'Belum ada karyawan', text: 'Tambahkan karyawan pertama agar akunnya bisa dipakai masuk dan dijadwalkan.' },
	ingredients: { title: 'Belum ada bahan', text: 'Tambahkan bahan pertama agar stok dan resep bisa dicatat.' },
	shiftCodes: { title: 'Belum ada kode shift', text: 'Tambahkan kode shift pertama agar jadwal bisa disusun.' },
	menuCategories: { title: 'Belum ada kategori menu', text: 'Tambahkan kategori pertama, misalnya Kopi atau Makanan, agar menu bisa dibuat dan tiketnya sampai ke stasiun yang tepat.', open: 'Buka Kategori Menu' },
	roles: { title: 'Belum ada peran', text: 'Tambahkan peran pertama untuk mengatur akses karyawan.' },
	branches: { title: 'Belum ada cabang', text: 'Tambahkan cabang pertama agar kas dan transaksi bisa dicatat per cabang.' },
	devices: { title: 'Belum ada perangkat', text: 'Tambahkan perangkat pertama untuk mulai mengelolanya.', action: 'Tambah perangkat' },
	paymentMethods: { title: 'Belum ada metode pembayaran', text: 'Tambahkan metode pertama agar kasir bisa menerima pembayaran.' },
	sop: { title: 'Belum ada SOP', text: 'Tambahkan SOP pertama agar karyawan bisa membacanya di aplikasi.' },
	batches: { title: 'Belum ada tugas outlet', text: 'Tambahkan tugas outlet pertama agar karyawan bisa mengisinya di aplikasi.' },
	expenses: { title: 'Belum ada pengeluaran', text: 'Catat pengeluaran pertama, atau ubah rentang tanggal lewat Filter untuk melihat periode lain.' },
	receipts: { title: 'Belum ada barang masuk', text: 'Catat barang masuk pertama, atau ubah rentang tanggal lewat Filter untuk melihat periode lain.' },
	losses: { title: 'Belum ada catatan', text: 'Catat bahan rusak pertama, atau ubah rentang tanggal lewat Filter untuk melihat periode lain.' },
	indirectIngredients: { title: 'Belum ada bahan tidak langsung', text: 'Tambahkan bahan yang tidak dipotong resep, seperti gas atau tisu, agar pemakaiannya bisa dicatat.' },
	usage: { title: 'Belum ada pemakaian', text: 'Catat pemakaian bahan tidak langsung pertama, atau ubah rentang tanggal lewat Filter untuk melihat periode lain.' }
} as const;
