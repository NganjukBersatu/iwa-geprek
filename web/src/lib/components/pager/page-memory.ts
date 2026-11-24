import { memoryKey, recall, remember } from '$lib/stores/memory';

/** The lists already brought back to their page since this screen was opened; opening the screen again clears it. */
let restored = new Set<string>();

/** Called when the person arrives on a screen, so its lists may go back to where they were left. */
export function enterScreen(): void {
	restored = new Set();
}

/** The page a list was left on, given once per visit of the screen. */
export function savedPage(path: string, unit: string): number | null {
	const key = memoryKey.page(path, unit);
	if (restored.has(key)) return null;
	restored.add(key);
	const saved = recall(key);
	return typeof saved === 'number' && Number.isInteger(saved) && saved > 1 ? saved : null;
}

export function rememberPage(path: string, unit: string, page: number): void {
	remember(memoryKey.page(path, unit), page > 1 ? page : null);
}
