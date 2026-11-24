import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { SalesBreakdown } from '$lib/api/types';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { salesBreakdownText } from '$lib/text/sales-breakdown';
import { rangeParams, type ReportQuery } from '../report/report.svelte';
import { orderTypeColumns, outletColumns } from './columns';

/** Penjualan per jenis pesanan dan per cabang, mengikuti cabang dan rentang laporan induknya. */
export class SalesBreakdownState {
	loading = $state(true);
	error = $state('');
	data = $state<SalesBreakdown | null>(null);
	private token = 0;

	readonly typeSort = new ListSort('penjualan-jenis-pesanan', sortKeys(orderTypeColumns), () => void this.load(this.query));
	readonly outletSort = new ListSort('penjualan-per-cabang', sortKeys(outletColumns), () => void this.load(this.query));

	constructor(private readonly queryOf: () => ReportQuery) {}

	get query(): ReportQuery {
		return this.queryOf();
	}

	async load(query: ReportQuery = this.query, quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) {
			this.loading = true;
			this.error = '';
		}
		try {
			const data = await api.reports.salesBreakdown({ ...rangeParams(query.range), type_sort: this.typeSort.param, outlet_sort: this.outletSort.param });
			if (token === this.token) this.data = data;
		} catch (failure) {
			if (token !== this.token || quiet) return;
			this.data = null;
			this.error = userMessage(failure, salesBreakdownText.loadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
