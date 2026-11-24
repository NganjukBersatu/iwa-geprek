import { api } from '$lib/api';
import type { Batch } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import type { FilterDef } from '$lib/components/filter/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { BRANCH_SORT } from '$lib/components/table/branch-column';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { branchList } from '$lib/stores/branch';
import { batchText } from '$lib/text/batches';
import { termText } from '$lib/text/terms';
import { ManageState } from '../manage/manage.svelte';
import { batchColumns } from './columns';
import { FILL_MODES, REPEAT_FILTER, STATUS_FILTER, type BatchKind } from './constants';

export const BATCH_TABLES = ['outlet_batches', 'outlet_batch_items', 'outlet_batch_runs', 'outlet_batch_answers'];

/** The list of one kind of task: outlet tasks or routine tasks. */
export class BatchesState extends ManageState<Batch> {
	override readonly tables = BATCH_TABLES;
	readonly columns: ReturnType<typeof batchColumns>;
	readonly sort: ListSort;
	readonly text: (typeof batchText.kinds)[BatchKind];
	readonly filters: Filters;

	constructor(readonly kind: BatchKind) {
		super();
		this.columns = batchColumns(kind);
		this.text = batchText.kinds[kind];
		const defs: FilterDef[] = [
			{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
			{ kind: 'select', key: 'status-tugas-rutin', label: batchText.filterStatus, options: STATUS_FILTER },
			{ kind: 'select', key: 'berulang-tugas-rutin', label: batchText.filterRepeat, options: REPEAT_FILTER }
		];
		if (kind === 'routine') defs.push({ kind: 'select', key: 'pengisi-tugas-rutin', label: batchText.filterFiller, options: FILL_MODES });
		this.filters = new Filters(defs);
		this.sort = new ListSort(kind === 'routine' ? 'tugas-rutin' : 'tugas-outlet', [...sortKeys(this.columns), BRANCH_SORT], () => void this.queryChanged());
	}

	get query(): { search: string | null; branch: string | null; active: string | null; repeat: string | null; fill: string | null } {
		return {
			search: this.search || null,
			branch: this.filters.get('cabang'),
			active: this.filters.get('status-tugas-rutin'),
			repeat: this.filters.get('berulang-tugas-rutin'),
			fill: this.kind === 'routine' ? this.filters.get('pengisi-tugas-rutin') : null
		};
	}

	protected async fetch(): Promise<void> {
		const outlets = await branchList();
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		const query = this.query;
		const page = await api.batches.list({
			kind: this.kind,
			q: query.search ?? undefined,
			active: query.active === null ? undefined : query.active === 'true',
			repeat: query.repeat ?? undefined,
			fill_mode: query.fill ?? undefined,
			outlet_id: query.branch ?? undefined,
			sort: this.sort.param,
			page: this.page,
			size: pageSize.value
		});
		this.items = page.items;
		this.total = page.total;
	}

	protected label(batch: Batch): string {
		return batch.name;
	}
}
