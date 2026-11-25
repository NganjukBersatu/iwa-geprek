import { memoryKey, remember } from '$lib/stores/memory';

// Tautan dari halaman lain membawa saringan lewat alamat; halaman tujuan membacanya dari memori filter yang sama.
const PARAM = { branch: 'cabang', search: 'cari', day: 'tanggal', until: 'sampai' } as const;
const DAY = /^\d{4}-\d{2}-\d{2}$/;

// day kosong ('') berarti rentang dikosongkan, supaya halaman tujuan memakai rentang bawaannya, bukan sisa pilihan halaman lain; null berarti tidak dikirim.
// until hanya berarti bersama day: rentang day sampai until untuk temuan yang mencakup beberapa hari.
export type LinkFilters = { branch?: string | null; search?: string | null; day?: string | null; until?: string | null };

// Alamat dasar hanya untuk mengurai jalur relatif; yang dikembalikan tetap jalur, query, dan hash milik tautan itu.
const PARSE_BASE = 'http://link.invalid';

/** Saringan ditambahkan ke query yang sudah ada di jalur (misalnya ?tab=…), bukan menimpanya atau membuat query kedua. */
export function withFilters(path: string, filters: LinkFilters): string {
	const url = new URL(path, PARSE_BASE);
	if (filters.branch) url.searchParams.set(PARAM.branch, filters.branch);
	if (filters.search) url.searchParams.set(PARAM.search, filters.search);
	if (filters.day !== undefined && filters.day !== null) url.searchParams.set(PARAM.day, filters.day);
	if (filters.day && filters.until) url.searchParams.set(PARAM.until, filters.until);
	return `${url.pathname}${url.search}${url.hash}`;
}

export function hasFilters(url: URL): boolean {
	return Object.values(PARAM).some((name) => url.searchParams.has(name));
}

// Dipanggil sebelum halaman tujuan dibuat, supaya daftarnya langsung memuat dengan saringan itu.
export function applyFilters(url: URL): void {
	const branch = url.searchParams.get(PARAM.branch);
	const search = url.searchParams.get(PARAM.search);
	const day = url.searchParams.get(PARAM.day);
	const until = url.searchParams.get(PARAM.until);
	if (branch) remember(memoryKey.filter('cabang'), branch);
	if (search !== null) remember(memoryKey.search(url.pathname), search.trim().slice(0, 100) || null);
	if (day !== null) remember(memoryKey.filter('rentang'), DAY.test(day) ? { from: day, to: until !== null && DAY.test(until) && until > day ? until : day } : null);
}

export function withoutFilters(url: URL): URL {
	const clean = new URL(url);
	for (const name of Object.values(PARAM)) clean.searchParams.delete(name);
	return clean;
}
