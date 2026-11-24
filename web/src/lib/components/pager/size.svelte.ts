import { memoryKey, recall, remember } from '$lib/stores/memory';

export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const DEFAULT_SIZE = 25;

function remembered(): number {
	const saved = recall(memoryKey.pageSize);
	return typeof saved === 'number' && PAGE_SIZE_OPTIONS.includes(saved) ? saved : DEFAULT_SIZE;
}

/** Rows per page for every list in the app; one choice per account, remembered in this browser. */
class PageSize {
	value = $state(DEFAULT_SIZE);

	/** Reads the signed-in account's choice; called once the account is known. */
	restore(): void {
		this.value = remembered();
	}

	set(size: number): void {
		if (!PAGE_SIZE_OPTIONS.includes(size)) return;
		this.value = size;
		remember(memoryKey.pageSize, size);
	}
}

export const pageSize = new PageSize();
