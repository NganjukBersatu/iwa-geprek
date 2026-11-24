import { api } from '$lib/api';
import type { BusyProductsParams, ProductSort, TimeUnit } from '$lib/api/reports';
import type { BusyProductRow, BusyProducts, Highlight } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { collectPages } from '../manage/collect';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { timeUnitFilters } from '../sales-peak/filters';
import { termText } from '$lib/text/terms';
import { productPeakText } from '$lib/text/product-peak';

export type ProductPeakQuery = ReportQuery & {
	unit: TimeUnit;
	hour: number | null;
	search: string;
	sort: ProductSort;
};

const SERIES = 5;

export const sortOptions = [
	{ value: 'qty', label: productPeakText.bestSelling },
	{ value: 'revenue', label: termText.revenue },
	{ value: 'time', label: productPeakText.byTime }
];

const unitNames: Record<TimeUnit | 'minute', string> = { hour: termText.hour, weekday: termText.day, date: termText.date, month: productPeakText.month, minute: productPeakText.minutes };

export class ProductPeakState extends ReportState<ProductPeakQuery, BusyProducts> {
	filters = createReportFilters([
		...timeUnitFilters,
		{ kind: 'select', key: 'urut', label: productPeakText.tableOrder, options: sortOptions, empty: 'qty' }
	]);

	hidden = $state<Set<string>>(new Set());

	get query(): ProductPeakQuery {
		const unit = (this.filters.get('satuan') ?? 'hour') as ProductPeakQuery['unit'];
		const hour = this.filters.get('jam');
		return {
			branch: this.filters.get('cabang'),
			range: this.filters.range('rentang'),
			unit,
			hour: unit === 'hour' && hour !== null ? Number(hour) : null,
			search: this.search,
			sort: (this.filters.get('urut') ?? 'qty') as ProductSort
		};
	}

	get unitName(): string {
		return unitNames[(this.data?.unit ?? this.query.unit) as keyof typeof unitNames];
	}

	get diving(): boolean {
		return this.data?.focus_hour !== null && this.data?.focus_hour !== undefined;
	}

	get unitHighlight(): Highlight | undefined {
		return this.data?.highlights.find((item) => item.metric === 'products');
	}

	get visibleSeries() {
		return (this.data?.series ?? []).filter((series) => !this.hidden.has(series.menu_item_name));
	}

	toggleSeries(name: string): void {
		const next = new Set(this.hidden);
		if (next.has(name)) next.delete(name);
		else if (next.size < (this.data?.series.length ?? 0) - 1) next.add(name);
		this.hidden = next;
	}

	leave(): void {
		this.filters.clear('jam');
	}

	protected fetch(query: ProductPeakQuery): Promise<BusyProducts> {
		return api.reports.busyProducts(this.params(query, this.page, pageSize.value));
	}

	async exportRows(): Promise<BusyProductRow[]> {
		const query = this.query;
		return collectPages(async (page, size) => {
			const result = await api.reports.busyProducts(this.params(query, page, size));
			return { items: result.rows, total: result.total_rows };
		});
	}

	private params(query: ProductPeakQuery, page: number, perPage: number): BusyProductsParams {
		return {
			...rangeParams(query.range),
			unit: query.unit,
			hour: query.hour ?? undefined,
			search: query.search || undefined,
			sort: query.sort,
			series: SERIES,
			page,
			per_page: perPage
		};
	}
}
