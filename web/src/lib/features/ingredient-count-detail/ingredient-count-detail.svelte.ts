import { controlText } from '$lib/text/controls';
import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { IngredientCountChanges, IngredientCountDetail, StockRow } from '$lib/api/types';
import { toast } from '$lib/components/feedback/toast.svelte';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { PAGES } from '$lib/nav/pages';
import { parseNumber } from '$lib/format/number';
import { changeColumns, lineStatus, STATUS_LABELS, type LineStatus } from './columns';
import { termText } from '$lib/text/terms';
import { ingredientCountDetailText } from '$lib/text/ingredient-count-detail';
import { format } from '$lib/text/format';

const INVALID_NUMBER = controlText.countedInvalid;

/** One closed count: its figures, the corrections an admin makes to them, and the record of who changed what. */
export class IngredientCountDetailState {
	detail = $state<IngredientCountDetail | null>(null);
	changes = $state<IngredientCountChanges | null>(null);
	loading = $state(true);
	error = $state('');
	search = $state('');
	bulk = $state(false);
	edited = $state<Record<string, string>>({});
	cancelling = $state(false);
	busy = $state(false);
	actionError = $state('');
	changesPage = $state(1);

	readonly changeSort = new ListSort('opname-perubahan', sortKeys(changeColumns), () => void this.loadChanges(1));

	readonly filters = new Filters([
		{
			kind: 'select',
			key: 'status_hitungan',
			label: termText.status,
			options: (Object.keys(STATUS_LABELS) as LineStatus[]).map((value) => ({ value, label: STATUS_LABELS[value] }))
		}
	]);

	constructor(
		readonly id: string,
		readonly partStart: string | null = null
	) {}

	/** Bagian yang ikut tertutup tidak punya hitungan sendiri, jadi tidak bisa diubah. */
	get ownPeriod(): boolean {
		return this.detail?.own_period ?? this.partStart === null;
	}

	get rows(): StockRow[] {
		return this.detail?.report.rows ?? [];
	}

	get visibleRows(): StockRow[] {
		const query = this.search.trim().toLowerCase();
		const status = this.filters.get('status_hitungan');
		return this.rows.filter((row) => (!query || row.name.toLowerCase().includes(query)) && (!status || lineStatus(row) === status));
	}

	get countedTotal(): number {
		return this.rows.filter((row) => row.counted !== null).length;
	}

	get uncountedRows(): StockRow[] {
		return this.rows.filter((row) => row.counted === null);
	}

	get differenceTotal(): number {
		return this.rows.filter((row) => lineStatus(row) === 'difference').length;
	}

	/** Every ingredient with stock at the end of the period was taken back to 0 when it closed. */
	get resetTotal(): number {
		return this.rows.filter((row) => Number(row.closing_stock) !== 0).length;
	}

	get editedCount(): number {
		return Object.values(this.edited).filter((text) => text.trim() !== '').length;
	}

	async load(): Promise<void> {
		this.loading = true;
		this.error = '';
		try {
			this.detail = await api.ingredientCounts.detail(this.id, this.partStart);
			await this.loadChanges(this.changesPage);
		} catch (error) {
			this.error = userMessage(error, ingredientCountDetailText.loadFailed);
		} finally {
			this.loading = false;
		}
	}

	/** Reloads quietly after a signal: what the screen shows stays until the new figures are in. */
	async refresh(): Promise<void> {
		try {
			this.detail = await api.ingredientCounts.detail(this.id, this.partStart);
			await this.loadChanges(this.changesPage);
		} catch {
			// The figures on screen stay; the next signal or a reload tries again.
		}
	}

	async loadChanges(page: number): Promise<void> {
		this.changesPage = page;
		if (this.partStart !== null) return;
		this.changes = await api.ingredientCounts.changes(this.id, this.changeSort.param, page, pageSize.value);
	}

	private async attempt<T>(work: () => Promise<T>, fallback: string): Promise<T | null> {
		this.busy = true;
		this.actionError = '';
		try {
			return await work();
		} catch (error) {
			this.actionError = userMessage(error, fallback);
			return null;
		} finally {
			this.busy = false;
		}
	}

	private async apply(lines: { ingredient_id: string; counted: string }[], message: string): Promise<boolean> {
		const result = await this.attempt(() => api.ingredientCounts.setLines(this.id, { lines }), ingredientCountDetailText.saveFailed);
		if (!result) return false;
		this.detail = result;
		await this.loadChanges(1);
		toast.show(message);
		return true;
	}

	startBulk(): void {
		this.actionError = '';
		this.edited = {};
		this.bulk = true;
	}

	stopBulk(): void {
		this.bulk = false;
		this.edited = {};
		this.actionError = '';
	}

	async saveBulk(): Promise<void> {
		const lines: { ingredient_id: string; counted: string }[] = [];
		for (const [ingredientId, text] of Object.entries(this.edited)) {
			if (!text.trim()) continue;
			const value = parseNumber(text);
			if (value === null || value < 0) {
				this.actionError = INVALID_NUMBER;
				return;
			}
			const current = this.rows.find((row) => row.ingredient_id === ingredientId)?.counted;
			if (current !== null && current !== undefined && Number(current) === value) continue;
			lines.push({ ingredient_id: ingredientId, counted: String(value) });
		}
		if (lines.length === 0) {
			this.actionError = ingredientCountDetailText.nothingChanged;
			return;
		}
		if (await this.apply(lines, format(ingredientCountDetailText.countedUpdatedCount, { count: lines.length }))) this.stopBulk();
	}

	askCancel(): void {
		this.actionError = '';
		this.cancelling = true;
	}

	async confirmCancel(): Promise<void> {
		const done = await this.attempt(() => api.ingredientCounts.cancel(this.id), ingredientCountDetailText.cancelFailed);
		if (done === null) return;
		this.cancelling = false;
		toast.show(ingredientCountDetailText.cancelled);
		await goto(PAGES.ingredientCounts.path);
	}

	closeDialogs(): void {
		this.cancelling = false;
		this.actionError = '';
	}
}
