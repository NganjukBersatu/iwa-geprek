import { ApiError } from '$lib/api/http';
import { userMessage } from '$lib/api/user-message';
import type { BulkResult } from '$lib/api/types';
import type { DateRange } from '$lib/date/range';
import { tick } from 'svelte';
import { rememberedSearch, rememberSearch } from '$lib/components/filter/search';
import { Selection } from '$lib/components/table/selection.svelte';
import { listText } from '$lib/text/lists';

/** Which list a bulk action works on, when a screen holds more than one. */
export type BulkScope = { selection: Selection; name: (id: string) => string };

export type BulkOutcome = { result: BulkResult; names: string[]; verb: string };

export abstract class ManageState<T extends { id: string }> {
	items = $state<T[]>([]);
	loading = $state(true);
	/** True once the first load has finished; from then on the page stays mounted while it reloads. */
	loaded = $state(false);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	/** The sentences of the fields the server refused in the last action, by field name; empty when none. */
	fieldErrors = $state<Record<string, string>>({});
	outcome = $state<BulkOutcome | null>(null);
	page = $state(1);
	total = $state(0);
	readonly selection = new Selection();

	/** Tables whose changes make this list reload by itself (see $lib/live); empty means it does not listen. */
	readonly tables: string[] = [];

	/** Rentang yang dipilih otomatis saat cabang dipilih; tidak ada berarti periode cabang yang sedang berjalan. */
	branchPeriod?(branchId: string): Promise<DateRange | null>;

	protected token = 0;

	protected abstract fetch(): Promise<void>;
	protected abstract label(row: T): string;

	/** What the list depends on besides the page; the shell reloads from the first page whenever it changes. */
	get query(): unknown {
		return null;
	}

	/** Free-text search of the list, kept apart from `filters` so it never shows as a filter. */
	search = $state(rememberedSearch());

	setSearch(query: string): void {
		this.search = query;
		rememberSearch(query);
		this.page = 1;
	}

	queryChanged(): Promise<void> {
		this.page = 1;
		return this.load();
	}

	setPage(page: number): void {
		this.page = page;
		void this.load();
	}

	/** Every row the filters match, not only the page on screen; a list that loads everything at once already holds them. */
	protected async allRows(): Promise<T[]> {
		return this.items;
	}

	/** What a download holds: the rows that are ticked, or, with nothing ticked, every row the filters match. */
	async exportRows(): Promise<T[]> {
		const rows = await this.allRows();
		return this.selection.count > 0 ? rows.filter((row) => this.selection.has(row.id)) : rows;
	}

	/** Reloads quietly, after an action or when the server says the data changed: the list stays as it is until the fresh rows arrive, so nothing dims or blinks. */
	async refresh(): Promise<void> {
		await this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		if (!quiet) this.error = '';
		try {
			await this.fetch();
		} catch (error) {
			if (token === this.token && !quiet) this.error = userMessage(error, listText.loadFailed);
		} finally {
			if (token === this.token) {
				this.loading = false;
				this.loaded = true;
			}
		}
	}

	/** Runs one action; true when it succeeded, with the message of a failure kept in actionError. */
	protected async attempt(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		this.busy = true;
		this.actionError = '';
		this.fieldErrors = {};
		try {
			await work();
			return true;
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			this.actionError = userMessage(error, fallback);
			return false;
		} finally {
			this.busy = false;
		}
	}

	private bulkNameOf(id: string): string {
		const row = this.items.find((item) => item.id === id);
		return row ? this.label(row) : id;
	}

	/** Runs an action on every selected row; rows that went through leave the selection, the rest stay for another try. [close] shuts the dialog that asked for it before the result is shown, so two dialogs never overlap. */
	protected async bulk(verb: string, work: (ids: string[]) => Promise<BulkResult>, close: () => void, scope: BulkScope = { selection: this.selection, name: (id) => this.bulkNameOf(id) }): Promise<void> {
		const ids = scope.selection.ids;
		const names = ids.map((id) => scope.name(id));
		let result: BulkResult | null = null;
		const done = await this.attempt(async () => {
			result = await work(ids);
		}, listText.bulkActionFailed);
		if (!done || result === null) return;
		for (const outcome of (result as BulkResult).results) {
			const id = ids[outcome.row - 1];
			if (outcome.ok && id) scope.selection.remove(id);
		}
		close();
		await tick();
		this.outcome = { result, names, verb };
		await this.refresh();
	}
}
