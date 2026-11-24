/** The standalone error page shown for an address that does not exist or a page that could not be served. */
export const errorPageText = {
	notFoundTitle: 'Halaman tidak ditemukan',
	notFoundBody: 'Alamat yang dibuka tidak ada atau sudah dipindahkan. Periksa alamatnya, atau kembali ke Dashboard.',
	forbiddenTitle: 'Tidak punya akses',
	forbiddenBody: 'Akun ini tidak diizinkan membuka halaman tersebut. Hubungi pemilik bila akses ini dibutuhkan.',
	serverTitle: 'Halaman tidak dapat dimuat',
	serverBody: 'Terjadi gangguan di server. Muat ulang sebentar lagi. Jika tetap gagal, hubungi admin.',
	otherTitle: 'Halaman tidak dapat dibuka',
	otherBody: 'Terjadi kendala saat membuka halaman ini. Kembali ke Dashboard, lalu coba lagi.',
	code: 'Kode {status}',
	back: 'Kembali ke Dashboard',
	reload: 'Muat ulang'
} as const;
