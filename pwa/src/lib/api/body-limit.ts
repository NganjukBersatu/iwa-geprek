import { REQUEST_MAX_BYTES } from '$lib/platform/upload-limits';

/** Batas bawaan adapter-node bila BODY_SIZE_LIMIT tidak diatur. */
const DEFAULT_LIMIT_BYTES = 512 * 1024;
const MULTIPLIERS: Record<string, number> = { K: 1024, M: 1024 ** 2, G: 1024 ** 3 };

/** Batas isi permintaan seperti dibaca adapter-node dari BODY_SIZE_LIMIT. */
export function bodyLimitBytes(raw: string | undefined): number {
	if (!raw) return DEFAULT_LIMIT_BYTES;
	const multiplier = MULTIPLIERS[raw.slice(-1).toUpperCase()];
	return multiplier === undefined ? Number(raw) : Number(raw.slice(0, -1)) * multiplier;
}

/** Kalimat masalah bila batas terlalu kecil untuk kiriman terbesar PWA; null bila cukup. */
export function bodyLimitProblem(raw: string | undefined): string | null {
	if (bodyLimitBytes(raw) >= REQUEST_MAX_BYTES) return null;
	return `BODY_SIZE_LIMIT (${raw ?? 'belum diatur, bawaan 512K'}) lebih kecil dari kiriman terbesar PWA (${REQUEST_MAX_BYTES} byte), sehingga unggahan besar ditolak 413. Jalankan server dengan "npm start" atau atur BODY_SIZE_LIMIT.`;
}
