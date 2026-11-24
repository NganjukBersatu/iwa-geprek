const PAGE_SIZE = 100;
const MAX_ROWS = 5000;

/** Reads a paged list to its end, a hundred rows at a time, and never more than a download can hold. */
export async function collectPages<T>(fetchPage: (page: number, size: number) => Promise<{ items: T[]; total: number }>): Promise<T[]> {
	const rows: T[] = [];
	for (let page = 1; rows.length < MAX_ROWS; page++) {
		const result = await fetchPage(page, PAGE_SIZE);
		rows.push(...result.items);
		if (result.items.length === 0 || rows.length >= result.total) break;
	}
	return rows.slice(0, MAX_ROWS);
}
