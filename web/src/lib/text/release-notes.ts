// Dibuat oleh scripts/generate-release.mjs dari app Android dan web karyawan. Jangan diubah tangan.

import type { ReleaseNote } from '$lib/features/download/release';

export const APK_VERSION = "1.0.1";

export const IOS_VERSION = "1.0.0";

export const APK_NOTES: ReleaseNote[] = [
	{ icon: "device-mobile", text: "Perangkat kasir kini nyaman dipakai di HP, tegak maupun mendatar" },
	{ icon: "shopping-bag", text: "Jenis pesanan awal mengikuti pengaturan cabang: makan di tempat atau dibawa pulang" },
	{ icon: "refresh", text: "Perangkat yang terlepas dapat dipasang ulang dengan kode tanpa keluar dari akun" },
];

export const IOS_NOTES: ReleaseNote[] = [
	{ icon: "user-check", text: "Absen masuk dan pulang dengan foto dan lokasi langsung dari ponsel" },
	{ icon: "calendar", text: "Jadwal kerja pribadi dapat dilihat kapan saja" },
	{ icon: "checklist", text: "Tugas harian dan tugas rutin dikerjakan dan dikirim lengkap dengan foto" },
	{ icon: "book", text: "Panduan kerja dapat dibaca langsung dari ponsel" },
];
