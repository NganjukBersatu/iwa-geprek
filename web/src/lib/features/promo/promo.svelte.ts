import { api } from '$lib/api';
import type { PromoReport } from '$lib/api/types';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { promoUsageColumns } from './columns';

export class PromoState extends ReportState<ReportQuery, PromoReport> {
	readonly sort = new ListSort('promo-laporan', sortKeys(promoUsageColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters();

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	protected fetch(query: ReportQuery): Promise<PromoReport> {
		return api.reports.promos({ ...rangeParams(query.range), sort: this.sort.param });
	}
}
