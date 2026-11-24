import { api } from '$lib/api';
import type { Overpayment, OverpaymentReport } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { collectPages } from '../manage/collect';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { overpaymentColumns } from './columns';

export class OverpaymentsState extends ReportState<ReportQuery, OverpaymentReport> {
	filters = createReportFilters();
	readonly sort = new ListSort('kelebihan-bayar', sortKeys(overpaymentColumns(true)), () => void this.queryChanged(this.query));

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	/** No branch chosen means every branch, so each row then needs its branch. */
	get allBranches(): boolean {
		return this.query.branch === null;
	}

	protected fetch(query: ReportQuery): Promise<OverpaymentReport> {
		return api.reports.overpayments({ ...rangeParams(query.range), sort: this.sort.param, page: this.page, per_page: pageSize.value });
	}

	async exportRows(): Promise<Overpayment[]> {
		const query = this.query;
		return collectPages(async (page, size) => {
			const result = await api.reports.overpayments({ ...rangeParams(query.range), sort: this.sort.param, page, per_page: size });
			return { items: result.rows, total: result.count };
		});
	}
}
