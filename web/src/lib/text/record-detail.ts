/** The sentences every record page shares, filled with the noun of the record (lower case, such as "catatan"). */
export type RecordText = {
	back: string;
	loading: string;
	loadFailed: string;
	retry: string;
	edit: string;
	remove: string;
	locked: string;
	saved: string;
	saveFailed: string;
	removeFailed: string;
	removeTitle: string;
};

const capital = (word: string): string => word.charAt(0).toUpperCase() + word.slice(1);

/** `backTo` is the name of the list the page returns to, such as "Catatan Pesanan". */
export function recordText(noun: string, backTo: string): RecordText {
	return {
		back: `Kembali ke ${backTo}`,
		loading: `Memuat ${noun}...`,
		loadFailed: `${capital(noun)} gagal dimuat`,
		retry: 'Coba lagi',
		edit: 'Ubah',
		remove: 'Hapus',
		locked: 'Tidak bisa diubah',
		saved: '{name} tersimpan.',
		saveFailed: `Gagal menyimpan ${noun}.`,
		removeFailed: `Gagal menghapus ${noun}.`,
		removeTitle: `Hapus ${noun}?`
	};
}

/** The sentences of a page that creates a record. */
export type CreateText = {
	loading: string;
	loadFailed: string;
	retry: string;
	created: string;
	createFailed: string;
};

export function createText(noun: string): CreateText {
	return {
		loading: 'Menyiapkan formulir...',
		loadFailed: 'Formulir gagal dimuat',
		retry: 'Coba lagi',
		created: `${capital(noun)} {name} ditambahkan.`,
		createFailed: `Gagal menyimpan ${noun}.`
	};
}
