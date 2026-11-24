import { memoryKey, recall, remember } from '$lib/stores/memory';

/** The list search the account typed last; every list starts from it and writes every change back. */
export function rememberedSearch(): string {
	const value = recall(memoryKey.search);
	return typeof value === 'string' ? value : '';
}

export function rememberSearch(query: string): void {
	remember(memoryKey.search, query || null);
}
