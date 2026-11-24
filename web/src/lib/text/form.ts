/** Sentences shared by the form components. */
export const formText = {
	showPassword: 'Tampilkan kata sandi',
	hidePassword: 'Sembunyikan kata sandi',
	characterLimit: 'Batas karakter tercapai.',
	chooseFile: 'Pilih berkas',
	noFile: 'Belum ada berkas',
	savedPhoto: 'Foto tersimpan',
	photoHint: 'JPG, PNG, atau WebP. Foto besar diperkecil otomatis.',
	preparingPhoto: 'Menyiapkan foto...',
	changePhoto: 'Ganti foto',
	savedPhotoHint: 'Foto tersimpan. Pilih atau tarik foto baru ke sini.',
	dropPhoto: 'Pilih atau tarik foto ke sini',
	previewUnavailable: 'Pratinjau tidak tersedia. Pilih foto lain.',
	pasteHint: 'Foto juga bisa ditempel dari papan klip.',
	filesChosen: '{count} berkas dipilih',
	readingPhoto: 'Membaca foto...',
	addFiles: 'Tambah berkas'
} as const;

/** Sentences of the question asked before leaving a form that was changed and not saved. */
export const unsavedText = {
	title: 'Perubahan belum disimpan',
	body: 'Isian yang Anda ubah belum disimpan. Jika keluar sekarang, perubahan itu akan hilang.',
	discard: 'Buang dan keluar',
	stay: 'Lanjut mengisi'
} as const;

/** Sentences of the form that has a page of its own. */
export const formPageText = {
	back: 'Kembali'
} as const;
