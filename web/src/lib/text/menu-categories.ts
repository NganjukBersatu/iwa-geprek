/** The sentences of the menu categories, added, edited, and removed from a dialog of their own list. */
export const menuCategoryText = {
	title: 'Kategori menu',
	description: 'Kategori mengelompokkan menu dan menentukan stasiun yang membuatnya, sehingga tiket pesanan sampai ke printer yang tepat.',
	removeTitle: 'Hapus kategori?',
	categoryName: 'Nama kategori',
	nameRequired: 'Nama kategori wajib diisi. Isi nama kelompok menu, misalnya Kopi.',
	addCategory: 'Tambah kategori',
	dialogDescription: 'Kategori mengelompokkan menu dan menentukan stasiun yang membuatnya. Stasiunnya diatur di Pengaturan Stasiun.',
	nameExample: 'Kopi',
	saveFailed: 'Gagal menyimpan kategori.',
	removeFailed: 'Gagal menghapus kategori.',
	categorySaved: 'Kategori {name} tersimpan.',
	categoryRemoved: 'Kategori {name} dihapus.',
	categoryRemoveNote: 'Kategori **{name}** dihapus beserta pengaturan stasiunnya. Kategori yang masih dipakai menu ditolak.',
	categoryInUse: 'Kategori ini dipakai {count} menu, jadi belum bisa dihapus. Pindahkan menunya ke kategori lain dulu.',
	categoryAdded: 'Kategori {name} ditambahkan.'
} as const;
