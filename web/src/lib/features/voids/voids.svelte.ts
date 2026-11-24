import { api } from '$lib/api';
import type { VoidReport } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { voidColumns } from './columns';

export class VoidsState extends ReportState<ReportQuery, VoidReport> {
	filters = createReportFilters();
	readonly sort = new ListSort('void', sortKeys(voidColumns), () => void this.queryChanged(this.query));

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	protected fetch(query: ReportQuery): Promise<VoidReport> {
		return api.reports.voids({ ...rangeParams(query.range), sort: this.sort.param, page: this.page, per_page: pageSize.value });
	}
}
