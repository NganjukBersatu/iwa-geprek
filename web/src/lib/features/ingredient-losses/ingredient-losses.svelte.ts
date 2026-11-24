import { api } from '$lib/api';
import type { IngredientMovement, WasteCause } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { STOCK_TABLES } from '$lib/live/tables';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { reportPresets } from '../report/filters';
import { branchList } from '$lib/stores/branch';
import { TRIAL, WASTE } from './kinds';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { lossColumns } from './columns';
import { termText } from '$lib/text/terms';

export type LossQuery = { search: string | null; branch: string | null; range: DateRange | null; kind: string };

export class IngredientLossesState extends ManageState<IngredientMovement> {
	override readonly tables = STOCK_TABLES;
	readonly sort = new ListSort('bahan-susut', sortKeys(lossColumns(WASTE)), () => void this.queryChanged());

	readonly filters = new Filters(
		[
			{
				kind: 'select',
				key: 'jenis_susut',
				label: termText.kind,
				options: [
					{ value: WASTE, label: termText.damaged },
					{ value: TRIAL, label: 'RnD' }
				]
			},
			{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
			{ kind: 'date', key: 'rentang', label: termText.range, presets: reportPresets, reach: 'past' }
		]
	);

	outlets = $state<{ id: string; name: string }[]>([]);
	causes = $state<WasteCause[]>([]);
	humanErrors = $state(0);
	natural = $state(0);

	get query(): LossQuery {
		return { search: this.search || null, branch: this.filters.get('cabang'), range: this.filters.range('rentang'), kind: this.filters.get('jenis_susut') ?? WASTE };
	}

	get kind(): string {
		return this.query.kind;
	}

	private params(page: number, size: number) {
		const query = this.query;
		return { kind: query.kind, search: query.search ?? undefined, start: query.range?.from, end: query.range?.to, sort: this.sort.param, page, size };
	}

	protected override allRows(): Promise<IngredientMovement[]> {
		return collectPages((page, size) => api.ingredientMovements.list(this.params(page, size)));
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [page, outlets, causes] = await Promise.all([
			api.ingredientMovements.list(this.params(this.page, pageSize.value)),
			branchList(),
			api.ingredientMovements.causes()
		]);
		this.outlets = outlets;
		this.causes = causes;
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		this.items = page.items;
		this.total = page.total;
		this.humanErrors = page.human_error_count;
		this.natural = page.natural_count;
	}

	protected label(movement: IngredientMovement): string {
		return movement.ingredient_name;
	}
}
