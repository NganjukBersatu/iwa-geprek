import { api } from '$lib/api';
import type { VisitorBreakdown } from '$lib/api/types';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { groupColumns, isDaySort } from './columns';
import { termText } from '$lib/text/terms';
import { visitorText } from '$lib/text/visitor';

export class VisitorState extends ReportState<ReportQuery, VisitorBreakdown> {
	readonly sort = new ListSort('pengunjung-hari', isDaySort, () => void this.queryChanged(this.query));
	readonly genderSort = new ListSort('pengunjung-gender', sortKeys(groupColumns), () => void this.queryChanged(this.query));
	readonly categorySort = new ListSort('pengunjung-kategori', sortKeys(groupColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters([
		{
			kind: 'select',
			key: 'ukuran',
			label: visitorText.chartSize,
			options: [
				{ value: 'transaksi', label: termText.transaction },
				{ value: 'omzet', label: termText.revenue }
			]
		},
		{
			kind: 'select',
			key: 'kelompok_grafik',
			label: visitorText.chartGroup,
			options: [
				{ value: 'gender', label: visitorText.gender },
				{ value: 'kategori', label: termText.category }
			]
		}
	]);

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	get metric(): 'transaksi' | 'omzet' {
		return this.filters.get('ukuran') === 'omzet' ? 'omzet' : 'transaksi';
	}

	get dimension(): 'gender' | 'kategori' {
		return this.filters.get('kelompok_grafik') === 'kategori' ? 'kategori' : 'gender';
	}

	protected fetch(query: ReportQuery): Promise<VisitorBreakdown> {
		return api.reports.visitors({ ...rangeParams(query.range), sort: this.sort.param, gender_sort: this.genderSort.param, category_sort: this.categorySort.param });
	}
}
