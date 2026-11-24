import { api } from '$lib/api';
import type { BatchRun } from '$lib/api/types';
import type { DateRange } from '$lib/date/range';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { BRANCH_SORT } from '$lib/components/table/branch-column';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { branchList } from '$lib/stores/branch';
import { batchRunText } from '$lib/text/batch-runs';
import { batchText } from '$lib/text/batches';
import { ManageState } from '../manage/manage.svelte';
import { reportPresets } from '../report/filters';
import { FOLLOW_UP_FILTER, PROBLEM_FILTER } from './constants';
import { runColumns } from './run-columns';

export type RunQuery = { search: string | null; branch: string | null; kind: string | null; problems: string | null; followUp: string | null; range: DateRange | null };

export const RUN_TABLES = ['outlet_batch_runs', 'outlet_batch_answers'];

/** The history of routine and outlet tasks that were filled: who filled them, when, and the answers. */
export class RunsState extends ManageState<BatchRun> {
	override readonly tables = RUN_TABLES;
	readonly sort = new ListSort('riwayat-tugas-outlet', [...sortKeys(runColumns), BRANCH_SORT], () => void this.queryChanged());

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: batchRunText.filterBranch, options: [] },
		{
			kind: 'select',
			key: 'jenis-tugas-rutin',
			label: batchRunText.filterKind,
			options: [
				{ value: 'routine', label: batchText.kinds.routine.title },
				{ value: 'outlet', label: batchText.kinds.outlet.title }
			]
		},
		{ kind: 'select', key: 'hasil-tugas-rutin', label: batchRunText.filterResult, options: PROBLEM_FILTER },
		{ kind: 'select', key: 'tindak-lanjut-tugas-rutin', label: batchRunText.filterFollowUp, options: FOLLOW_UP_FILTER },
		{ kind: 'date', key: 'rentang', label: batchRunText.filterRange, presets: reportPresets, reach: 'past' }
	]);

	get query(): RunQuery {
		return {
			search: this.search || null,
			branch: this.filters.get('cabang'),
			kind: this.filters.get('jenis-tugas-rutin'),
			problems: this.filters.get('hasil-tugas-rutin'),
			followUp: this.filters.get('tindak-lanjut-tugas-rutin'),
			range: this.filters.range('rentang')
		};
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [outlets, page] = await Promise.all([
			branchList(),
			api.batches.runs({
				date_from: query.range?.from,
				date_to: query.range?.to,
				outlet_id: query.branch ?? undefined,
				kind: query.kind ?? undefined,
				q: query.search ?? undefined,
				follow_up: query.followUp ?? undefined,
				problems: query.problems === null ? undefined : query.problems === 'true',
				sort: this.sort.param,
				page: this.page,
				size: pageSize.value
			})
		]);
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		this.items = page.items;
		this.total = page.total;
	}

	protected label(run: BatchRun): string {
		return run.batch_name;
	}
}
