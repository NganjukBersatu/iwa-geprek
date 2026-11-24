import { api } from '$lib/api';
import type { TimeUnit } from '$lib/api/reports';
import type { BusySales, Highlight } from '$lib/api/types';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { metricOptions, timeUnitFilters } from './filters';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { peakColumns } from './columns';
import { termText } from '$lib/text/terms';
import { salesPeakText } from '$lib/text/sales-peak';

export type PeakMetric = 'sales' | 'transactions' | 'customers';
export type PeakQuery = ReportQuery & { unit: TimeUnit; hour: number | null };

const unitNames: Record<TimeUnit | 'minute', string> = { hour: termText.hour, weekday: termText.day, date: termText.date, month: salesPeakText.month, minute: salesPeakText.minutes };

export class SalesPeakState extends ReportState<PeakQuery, BusySales> {
	readonly sort = new ListSort('jam-ramai', sortKeys(peakColumns('')), () => void this.queryChanged(this.query));

	filters = createReportFilters([...timeUnitFilters, { kind: 'select', key: 'metrik', label: salesPeakText.metric, options: metricOptions }]);

	get query(): PeakQuery {
		const unit = (this.filters.get('satuan') ?? 'hour') as PeakQuery['unit'];
		const hour = this.filters.get('jam');
		return {
			branch: this.filters.get('cabang'),
			range: this.filters.range('rentang'),
			unit,
			hour: unit === 'hour' && hour !== null ? Number(hour) : null
		};
	}

	get unitName(): string {
		return unitNames[(this.data?.unit ?? this.query.unit) as keyof typeof unitNames];
	}

	get repeating(): boolean {
		return this.query.unit === 'hour' || this.query.unit === 'weekday';
	}

	get diving(): boolean {
		return this.data?.focus_hour !== null && this.data?.focus_hour !== undefined;
	}

	get metrics(): PeakMetric[] {
		const chosen = this.filters.get('metrik') as PeakMetric | null;
		return chosen ? [chosen] : metricOptions.map((option) => option.value as PeakMetric);
	}

	get salesHighlight(): Highlight | undefined {
		return this.data?.highlights.find((item) => item.metric === 'sales');
	}

	get trafficHighlight(): Highlight | undefined {
		return this.data?.highlights.find((item) => item.metric === 'transactions');
	}

	get peaksDiffer(): boolean {
		const sales = this.salesHighlight?.peak_label;
		const traffic = this.trafficHighlight?.peak_label;
		return Boolean(sales && traffic && sales !== traffic);
	}

	value(metric: PeakMetric, index: number): number {
		const row = this.data?.rows[index];
		if (!row) return 0;
		return Number(this.repeating ? row[`${metric}_average`] : row[metric]);
	}

	dive(index: number): void {
		const key = this.data?.rows[index]?.key;
		if (key !== undefined && this.query.unit === 'hour' && !this.diving) this.filters.set('jam', key);
	}

	leave(): void {
		this.filters.clear('jam');
	}

	protected fetch(query: PeakQuery): Promise<BusySales> {
		return api.reports.busySales({ ...rangeParams(query.range), unit: query.unit, hour: query.hour ?? undefined, sort: this.sort.param });
	}
}
