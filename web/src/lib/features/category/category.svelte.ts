import { api } from '$lib/api';
import type { CategoryReport, MenuSales } from '$lib/api/types';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { categoryColumns, menuColumns, unsoldColumns } from './columns';
import { categoryReportText } from '$lib/text/category-report';

export type UnsoldEmptyReason = 'noMenu' | 'search' | 'hidden' | 'allSold';

export class CategoryState extends ReportState<ReportQuery, CategoryReport> {
	readonly sort = new ListSort('kategori', sortKeys(categoryColumns), () => void this.queryChanged(this.query));
	readonly menuSort = new ListSort('kategori-menu', sortKeys(menuColumns), () => void this.queryChanged(this.query));
	readonly unsoldSort = new ListSort('kategori-tidak-laku', sortKeys(unsoldColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters([
		{ kind: 'select', key: 'tampil', label: categoryReportText.unsoldMenus, options: [{ value: 'semua', label: categoryReportText.includeHidden }] },
	]);

	get query(): ReportQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	menusOf(category: string): MenuSales[] {
		return (this.data?.menus ?? []).filter((menu) => menu.category === category);
	}

	get unsold() {
		const showHidden = this.filters.get('tampil') === 'semua';
		const term = this.search.toLowerCase();
		return (this.data?.unsold ?? []).filter((item) => (showHidden || item.is_available) && (!term || item.name.toLowerCase().includes(term)));
	}

	/** Why the unsold list shows nothing, so each reason says its own thing; null while there is something to show or nothing has loaded. */
	get unsoldEmptyReason(): UnsoldEmptyReason | null {
		if (!this.data || this.unsold.length > 0) return null;
		if (this.data.total_menu_count === 0) return 'noMenu';
		if (this.search) return 'search';
		if (this.data.unsold.length > 0) return 'hidden';
		return 'allSold';
	}

	protected fetch(query: ReportQuery): Promise<CategoryReport> {
		return api.reports.categories({ ...rangeParams(query.range), sort: this.sort.param, menu_sort: this.menuSort.param, unsold_sort: this.unsoldSort.param });
	}
}
