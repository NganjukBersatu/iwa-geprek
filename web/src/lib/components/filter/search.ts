import { memoryKey, recall, remember } from '$lib/stores/memory';

/** The search the account typed last on this screen; each screen keeps its own, so a word looked up on one list never empties another. */
export function rememberedSearch(path: string): string {
	const value = recall(memoryKey.search(path));
	return typeof value === 'string' ? value : '';
}

export function rememberSearch(path: string, query: string): void {
	remember(memoryKey.search(path), query || null);
}
