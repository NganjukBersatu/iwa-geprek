import { api } from '$lib/api';
import type { StockReport } from '$lib/api/types';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { STOCK_TABLES } from '$lib/live/tables';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { stockColumns } from './columns';

export class StockState extends ReportState<ReportQuery, StockReport> {
	override readonly tables = STOCK_TABLES;
	readonly sort = new ListSort('stok-bahan', sortKeys(stockColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters();

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	get rows() {
		const term = this.search.toLowerCase();
		const all = this.data?.rows ?? [];
		return term ? all.filter((row) => row.name.toLowerCase().includes(term)) : all;
	}

	protected fetch(query: ReportQuery): Promise<StockReport> {
		return api.reports.ingredientStock({ ...rangeParams(query.range), sort: this.sort.param });
	}
}
