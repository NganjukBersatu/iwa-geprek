import { memoryKey, remember } from '$lib/stores/memory';

// Tautan dari halaman lain membawa saringan lewat alamat; halaman tujuan membacanya dari memori filter yang sama.
const PARAM = { branch: 'cabang', search: 'cari', day: 'tanggal' } as const;
const DAY = /^\d{4}-\d{2}-\d{2}$/;

export type LinkFilters = { branch?: string | null; search?: string | null; day?: string | null };

export function withFilters(path: string, filters: LinkFilters): string {
	const params = new URLSearchParams();
	if (filters.branch) params.set(PARAM.branch, filters.branch);
	if (filters.search) params.set(PARAM.search, filters.search);
	if (filters.day) params.set(PARAM.day, filters.day);
	const query = params.toString();
	return query ? `${path}?${query}` : path;
}

export function hasFilters(url: URL): boolean {
	return Object.values(PARAM).some((name) => url.searchParams.has(name));
}

// Dipanggil sebelum halaman tujuan dibuat, supaya daftarnya langsung memuat dengan saringan itu.
export function applyFilters(url: URL): void {
	const branch = url.searchParams.get(PARAM.branch);
	const search = url.searchParams.get(PARAM.search);
	const day = url.searchParams.get(PARAM.day);
	if (branch) remember(memoryKey.filter('cabang'), branch);
	if (search !== null) remember(memoryKey.search, search.trim().slice(0, 100) || null);
	if (day && DAY.test(day)) remember(memoryKey.filter('rentang'), { from: day, to: day });
}

export function withoutFilters(url: URL): URL {
	const clean = new URL(url);
	for (const name of Object.values(PARAM)) clean.searchParams.delete(name);
	return clean;
}
