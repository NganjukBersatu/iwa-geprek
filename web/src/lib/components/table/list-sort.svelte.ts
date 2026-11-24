import { memoryKey, recall, remember } from '$lib/stores/memory';

export type SortOrder = { kind: 'default' } | { kind: 'column'; key: string; descending: boolean };
export type SortDirection = 'none' | 'ascending' | 'descending';

const DEFAULT: SortOrder = { kind: 'default' };

/** The columns a list can be ordered by: a fixed list, or a rule for lists whose columns follow the data. */
export type Offered = readonly string[] | ((key: string) => boolean);

function orderOf(param: unknown, offered: Offered): SortOrder {
	if (typeof param !== 'string' || !/^-?[a-z_][a-z0-9_]{0,39}$/.test(param)) return DEFAULT;
	const key = param.replace(/^-/, '');
	// A remembered column the list no longer offers is dropped, so the server never refuses a stale order.
	return (typeof offered === 'function' ? offered(key) : offered.includes(key)) ? { kind: 'column', key, descending: param.startsWith('-') } : DEFAULT;
}

/** The sortable keys of a list's columns, the one place a list states what it can be ordered by. */
export function sortKeys(columns: { sort?: string }[]): string[] {
	return columns.flatMap((column) => (column.sort ? [column.sort] : []));
}

/** The order a person picked for one list, remembered per account under the list's id; the server applies it, never the browser. */
export class ListSort {
	order = $state<SortOrder>(DEFAULT);

	constructor(
		private readonly list: string,
		offered: Offered,
		private readonly onchange: () => void
	) {
		this.order = orderOf(recall(memoryKey.sort(list)), offered);
	}

	/** What the API receives: the column key, "-" in front for descending; nothing keeps the list's own order. */
	get param(): string | undefined {
		return this.order.kind === 'column' ? `${this.order.descending ? '-' : ''}${this.order.key}` : undefined;
	}

	direction(key: string): SortDirection {
		if (this.order.kind !== 'column' || this.order.key !== key) return 'none';
		return this.order.descending ? 'descending' : 'ascending';
	}

	/** Ascending, then descending, then the list's own order again. */
	toggle(key: string): void {
		const now = this.direction(key);
		this.set(now === 'none' ? { kind: 'column', key, descending: false } : now === 'ascending' ? { kind: 'column', key, descending: true } : DEFAULT);
	}

	set(order: SortOrder): void {
		this.order = order;
		remember(memoryKey.sort(this.list), this.param ?? null);
		this.onchange();
	}
}
