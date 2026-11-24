import { api } from '$lib/api';
import type { MarginItem, MarginReport } from '$lib/api/types';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { marginColumns } from './columns';

export class MarginState extends ReportState<ReportQuery, MarginReport> {
	readonly sort = new ListSort('margin', sortKeys(marginColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters();

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	get matching(): MarginItem[] {
		const term = this.search.toLowerCase();
		const all = this.data?.items ?? [];
		return term ? all.filter((item) => item.menu_item_name.toLowerCase().includes(term)) : all;
	}

	protected override readonly paging = 'client';

	get pageRows(): MarginItem[] {
		return this.pageOf(this.matching).rows;
	}

	protected fetch(query: ReportQuery): Promise<MarginReport> {
		return api.reports.margin({ ...rangeParams(query.range), sort: this.sort.param });
	}
}
