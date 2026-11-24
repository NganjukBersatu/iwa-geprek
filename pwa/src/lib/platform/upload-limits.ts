/** Batas kiriman berkas dari PWA; satu sumber supaya batas isi permintaan di server web tidak pernah lebih kecil dari kiriman terbesar. */

/** Di bawah 2 MB, batas terketat di server (foto profil), supaya hasilnya diterima di mana pun. */
export const PHOTO_MAX_BYTES = 1_800_000;
export const VIDEO_MAX_BYTES = 30 * 1024 * 1024;
export const PDF_MAX_BYTES = 5 * 1024 * 1024;

export const MEDIA_MAX_PHOTOS = 5;
export const MEDIA_MAX_VIDEOS = 1;
/** Sama dengan MAX_ITEMS di web/management/batches/constants.py; setiap item foto tugas outlet mengirim satu foto. */
export const BATCH_MAX_PHOTOS = 50;

/** Ruang untuk isian teks dan pembatas bagian multipart. */
const FORM_OVERHEAD_BYTES = 1024 * 1024;

const LARGEST_UPLOAD_BYTES = Math.max(
	BATCH_MAX_PHOTOS * PHOTO_MAX_BYTES,
	MEDIA_MAX_PHOTOS * PHOTO_MAX_BYTES + MEDIA_MAX_VIDEOS * VIDEO_MAX_BYTES,
	PDF_MAX_BYTES
);

/** Ukuran isi permintaan terbesar yang mungkin dikirim PWA. */
export const REQUEST_MAX_BYTES = LARGEST_UPLOAD_BYTES + FORM_OVERHEAD_BYTES;
