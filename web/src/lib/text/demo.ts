import { brand } from '$lib/text/brand';

/** The sentences of the demo mode: the button on the sign-in page, the loading screen, and the strip shown while it runs. */
export const demoText = {
	or: 'atau',
	tryDemo: 'Coba mode demo',
	tryDemoHint: `Lihat ${brand.name} berjalan dengan data contoh`,
	loadingTitle: 'Menyiapkan mode demo',
	loadingNote: 'Mohon tunggu sebentar.',
	steps: {
		preparing: 'Menyiapkan data',
		loading: 'Memuat menu, penjualan, stok, dan absensi',
		linking: 'Menyambungkan perangkat',
		ready: 'Siap'
	},
	progressLabel: 'Kemajuan memuat data demo',
	percent: '{percent}%',
	failedTitle: 'Mode demo belum bisa disiapkan',
	failedOnServer: 'Coba lagi beberapa saat lagi.',
	tooLong: 'Coba lagi beberapa saat lagi.',
	backToSignIn: 'Kembali ke halaman masuk',
	bar: 'Mode demo',
	exit: 'Keluar mode demo',
	exitTitle: 'Keluar mode demo?',
	exitBody: 'Anda akan kembali ke halaman masuk.',
	exitConfirm: 'Ya, keluar',
	exitFailed: 'Belum bisa keluar dari mode demo. Coba lagi.'
} as const;
