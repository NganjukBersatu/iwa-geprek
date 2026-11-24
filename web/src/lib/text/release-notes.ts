// Dibuat oleh scripts/generate-release.mjs dari app Android dan web karyawan. Jangan diubah tangan.

import type { ReleaseNote } from '$lib/features/download/release';

export const APK_VERSION = "1.0.0";

export const IOS_VERSION = "1.0.0";

export const APK_NOTES: ReleaseNote[] = [
	{ icon: "shopping-cart", text: "Kasir untuk mencatat pesanan dan menerima pembayaran tunai maupun nontunai" },
	{ icon: "receipt", text: "Pesanan dapat disimpan sebagai tagihan terbuka dan dibayar belakangan" },
	{ icon: "printer", text: "Struk dan tiket dapur dicetak langsung ke printer yang terhubung" },
	{ icon: "clipboard-list", text: "Stok bahan berkurang otomatis mengikuti resep setiap menu yang terjual" },
	{ icon: "qrcode", text: "Absen karyawan lewat kode QR di tablet" },
];

export const IOS_NOTES: ReleaseNote[] = [
	{ icon: "user-check", text: "Absen masuk dan pulang dengan foto dan lokasi langsung dari ponsel" },
	{ icon: "calendar", text: "Jadwal kerja pribadi dapat dilihat kapan saja" },
	{ icon: "checklist", text: "Tugas harian dan tugas rutin dikerjakan dan dikirim lengkap dengan foto" },
	{ icon: "book", text: "Panduan kerja dapat dibaca langsung dari ponsel" },
];
