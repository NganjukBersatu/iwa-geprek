// Dibuat oleh scripts/generate-release.mjs dari app Android dan web karyawan. Jangan diubah tangan.

import type { ReleaseNote } from '$lib/features/download/release';

export const APK_VERSION = "0.1.0";

export const IOS_VERSION = "0.1.0";

export const APK_NOTES: ReleaseNote[] = [
	{ icon: "calendar-check", text: "Tugas rutin tampil terpisah dari tugas lain, hanya untuk penerimanya pada hari yang dijadwalkan" },
	{ icon: "checklist", text: "Halaman Tugas dikelompokkan per jenis, dengan tab Belum selesai dan Selesai di bawah kolom cari" },
	{ icon: "refresh", text: "Tugas yang sudah dikirim dapat diperbaiki, dibatalkan, atau dihapus" },
	{ icon: "file-text", text: "Tugas tindak lanjut menampilkan pengisian asalnya, lengkap dengan jawaban dan foto" },
	{ icon: "photo-off", text: "Foto yang gagal dimuat diberi keterangan dan dapat dimuat ulang dengan satu ketukan" },
	{ icon: "category", text: "Menu di Kasir diurutkan abjad dalam setiap kategori" },
];

export const IOS_NOTES: ReleaseNote[] = [
	{ icon: "calendar-check", text: "Tugas rutin tampil terpisah dari tugas lain, hanya untuk penerimanya pada hari yang dijadwalkan" },
	{ icon: "checklist", text: "Halaman Tugas dikelompokkan per jenis, dengan tab Belum selesai dan Selesai di bawah kolom cari" },
	{ icon: "refresh", text: "Tugas yang sudah dikirim dapat diperbaiki, dibatalkan, atau dihapus" },
	{ icon: "clipboard-check", text: "Tugas tindak lanjut menampilkan pengisian asalnya, lengkap dengan jawaban dan foto" },
];
