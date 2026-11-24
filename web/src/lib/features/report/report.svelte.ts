import { userMessage } from '$lib/api/user-message';
import type { DateParams } from '$lib/api/reports';
import type { Filters } from '$lib/components/filter/filters.svelte';
import { rememberedSearch, rememberSearch } from '$lib/components/filter/search';
import { formatRange, type DateRange } from '$lib/date/range';
import { pageOf } from '$lib/components/pager/page-of';
import { SALES_TABLES } from '$lib/live/tables';
import { listText } from '$lib/text/lists';

export type ReportQuery = { branch: string | null; range: DateRange | null };

export const rangeParams = (range: DateRange | null): DateParams => (range ? { start: range.from, end: range.to } : {});

export abstract class ReportState<Q extends ReportQuery, D extends { start: string; end: string }> {
	abstract filters: Filters;
	abstract get query(): Q;
	protected abstract fetch(query: Q): Promise<D>;

	loading = $state(true);
	error = $state('');
	data = $state<D | null>(null);
	page = $state(1);

	/** Tables whose changes reload this report by itself (see $lib/live). */
	readonly tables: string[] = SALES_TABLES;
	protected readonly paging: 'server' | 'client' = 'server';
	private token = 0;

	get range(): DateRange | null {
		const chosen = this.query.range;
		if (chosen) return chosen;
		return this.data ? { from: this.data.start, to: this.data.end } : null;
	}

	get periodLabel(): string {
		const range = this.range;
		return range ? formatRange(range) : 'periode bawaan';
	}

	/** Free-text search of the list, kept apart from `filters` so it never shows as a filter. */
	search = $state(rememberedSearch());

	setSearch(query: string): void {
		this.search = query;
		rememberSearch(query);
		this.page = 1;
	}

	queryChanged(query: Q): Promise<void> {
		this.page = 1;
		return this.load(query);
	}

	setPage(page: number): void {
		this.page = page;
		if (this.paging === 'server') void this.load();
	}

	pageOf<T>(items: T[]): { rows: T[]; page: number } {
		return pageOf(items, this.page);
	}

	setBranches(options: { value: string; label: string }[]): void {
		this.filters.setOptions('cabang', options);
	}

	/** Reloads without dimming or clearing: what the screen shows stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(this.query, true);
	}

	async load(query: Q = this.query, quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		if (!quiet) this.error = '';
		try {
			const data = await this.fetch(query);
			if (token === this.token) this.data = data;
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.data = null;
			this.error = userMessage(error, listText.reportLoadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
