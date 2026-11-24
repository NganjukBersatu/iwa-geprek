import { api } from '$lib/api';
import type { IngredientMovement } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { STOCK_TABLES } from '$lib/live/tables';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { receiptColumns } from './columns';
import { reportPresets } from '../report/filters';
import { branchList } from '$lib/stores/branch';
import { termText } from '$lib/text/terms';

const KIND = 'masuk';

export type ReceiptQuery = { search: string | null; branch: string | null; range: DateRange | null };

export class IngredientReceiptsState extends ManageState<IngredientMovement> {
	override readonly tables = STOCK_TABLES;
	readonly sort = new ListSort('bahan-masuk', sortKeys(receiptColumns), () => void this.queryChanged());

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{ kind: 'date', key: 'rentang', label: termText.range, presets: reportPresets, reach: 'past' }
	]);

	outlets = $state<{ id: string; name: string }[]>([]);

	get query(): ReceiptQuery {
		return { search: this.search || null, branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	private params(page: number, size: number) {
		const query = this.query;
		return { kind: KIND, search: query.search ?? undefined, start: query.range?.from, end: query.range?.to, sort: this.sort.param, page, size };
	}

	protected override allRows(): Promise<IngredientMovement[]> {
		return collectPages((page, size) => api.ingredientMovements.list(this.params(page, size)));
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [page, outlets] = await Promise.all([
			api.ingredientMovements.list(this.params(this.page, pageSize.value)),
			branchList()
		]);
		this.outlets = outlets;
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		this.items = page.items;
		this.total = page.total;
	}

	protected label(movement: IngredientMovement): string {
		return movement.ingredient_name;
	}
}
