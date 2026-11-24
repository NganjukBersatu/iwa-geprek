/** Every sentence an error can become, by the stable code the server (or this app) gives it; {minutes} and {requestId} are filled in. */
export const errorText = {
	unknown: 'Terjadi kendala. Coba lagi, atau hubungi admin jika tetap gagal.',
	serverWithReference: 'Terjadi gangguan di server. Coba lagi sebentar lagi. Jika tetap gagal, hubungi admin dan sebutkan kode {requestId}.',
	server: 'Terjadi gangguan di server. Coba lagi sebentar lagi. Jika tetap gagal, hubungi admin.',
	codes: {
		OFFLINE: 'Server tidak bisa dihubungi. Periksa koneksi internet, lalu coba lagi.',
		UNAVAILABLE: 'Server sedang tidak dapat dihubungi. Tunggu sebentar, lalu coba lagi.',
		STORAGE_UNAVAILABLE: 'Berkas belum dapat disimpan karena penyimpanan sedang bermasalah. Coba lagi sebentar lagi. Jika tetap gagal, hubungi admin.',
		UNREADABLE_RESPONSE: 'Balasan dari server tidak bisa dibaca. Coba lagi; kalau terus begini, hubungi admin.',
		INVALID_CREDENTIALS: 'Nama pengguna atau kata sandi salah. Periksa lagi, lalu coba ulang.',
		ACCOUNT_DISABLED: 'Akun ini tidak aktif. Hubungi admin atau pemilik.',
		TOO_MANY_LOGIN_ATTEMPTS: 'Terlalu banyak percobaan masuk yang gagal. Coba lagi dalam {minutes} menit.',
		TOO_MANY_PAIRING_ATTEMPTS: 'Terlalu banyak kode perangkat yang salah. Coba lagi dalam {minutes} menit.',
		SESSION_INVALID: 'Sesi Anda telah berakhir. Masuk kembali untuk melanjutkan.',
		PERMISSION_DENIED: 'Anda tidak memiliki akses untuk tindakan ini. Hubungi admin jika Anda memerlukannya.',
		FULL_ACCESS_REQUIRED: 'Halaman ini sementara hanya untuk peran dengan akses penuh.',
		FOREIGN_SITE: 'Permintaan ditolak karena berasal dari situs lain. Buka aplikasi langsung dari alamatnya, lalu coba lagi.',
		QUERY_TOO_LONG: 'Permintaan ini terlalu berat dan dibatalkan. Persempit rentang atau filternya, lalu coba lagi.',
		TOO_MANY_REQUESTS: 'Terlalu banyak permintaan dalam waktu singkat. Tunggu sebentar, lalu coba lagi.'
	} as Record<string, string>,
	// What a status means when the server named no rule and wrote no sentence of its own.
	statuses: {
		400: 'Permintaan tidak dapat diproses. Periksa isian Anda, lalu coba lagi.',
		401: 'Sesi Anda telah berakhir. Masuk kembali untuk melanjutkan.',
		403: 'Anda tidak memiliki akses untuk tindakan ini. Hubungi admin jika Anda memerlukannya.',
		404: 'Data yang diminta tidak ditemukan. Muat ulang halaman, lalu coba lagi.',
		409: 'Data bentrok dengan yang sudah ada. Muat ulang halaman, lalu coba lagi.',
		413: 'Data yang dikirim terlalu besar. Kurangi ukurannya, lalu kirim ulang.',
		429: 'Terlalu banyak permintaan dalam waktu singkat. Tunggu sebentar, lalu coba lagi.'
	} as Record<number, string>
} as const;
