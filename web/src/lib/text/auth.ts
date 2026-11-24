import { brand } from '$lib/text/brand';
/** Every sentence of signing in and out. */
export const authText = {
	login: {
		pageTitle: `Masuk - ${brand.name}`,
		heading: 'Masuk sebagai admin',
		imageAlt: brand.storefrontCaption,
		logoAlt: `Logo ${brand.name}`,
		username: { label: 'Nama pengguna', placeholder: 'Masukkan nama pengguna', required: 'Nama pengguna belum diisi. Masukkan nama pengguna Anda.' },
		password: { label: 'Kata sandi', placeholder: 'Masukkan kata sandi', required: 'Kata sandi belum diisi. Masukkan kata sandi Anda.' },
		submit: 'Masuk',
		submitting: 'Memproses...',
		forgotPassword: 'Lupa kata sandi? Hubungi pemilik untuk mengatur ulang.',
		noWebAccess: 'Akun ini tidak punya akses ke web.'
	},
	signOutTitle: 'Keluar dari akun?',
	signOutBody: 'Anda perlu masuk lagi untuk memakai web ini.',
	signOutUnsavedBody: 'Perubahan yang belum disimpan akan hilang, dan Anda perlu masuk lagi untuk memakai web ini.',
	signOutConfirm: 'Keluar',
	signOutFailed: 'Gagal keluar. Periksa koneksi, lalu coba lagi.',
	noAccessTitle: 'Tidak punya akses',
	noAccessBody: 'Peran akun ini tidak diizinkan membuka halaman tersebut. Hubungi pemilik bila akses ini dibutuhkan.',
	noAccessBack: 'Kembali ke {page}'
} as const;
