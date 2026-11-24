import { api } from '$lib/api';
import type { MutationPage } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { EXPENSE_TABLES } from '$lib/live/tables';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { mutationColumns } from './columns';

export class MutationsState extends ReportState<ReportQuery, MutationPage> {
	override readonly tables = EXPENSE_TABLES;
	readonly sort = new ListSort('mutasi', sortKeys(mutationColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters();

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	protected fetch(query: ReportQuery): Promise<MutationPage> {
		return api.mutations.list({ ...rangeParams(query.range), sort: this.sort.param, page: this.page, size: pageSize.value });
	}
}
