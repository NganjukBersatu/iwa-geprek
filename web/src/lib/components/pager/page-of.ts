import { pageSize } from './size.svelte';

export function pageOf<T>(items: T[], page: number): { rows: T[]; page: number } {
	const current = Math.min(page, Math.max(1, Math.ceil(items.length / pageSize.value)));
	return { rows: items.slice((current - 1) * pageSize.value, current * pageSize.value), page: current };
}
