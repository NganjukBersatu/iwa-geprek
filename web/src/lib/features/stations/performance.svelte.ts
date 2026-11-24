import { controlText } from '$lib/text/controls';
import { api } from '$lib/api';
import type { KitchenReport, StationPerformance } from '$lib/api/types';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { STATION_TABLES } from '$lib/live/tables';
import { hourColumns, orderColumns } from './served-columns';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { termText } from '$lib/text/terms';
import { stationText } from '$lib/text/stations';
import { format } from '$lib/text/format';

export type PerformanceQuery = ReportQuery & { station: string | null; threshold: number };
export type PerformanceData = { start: string; end: string; station: StationPerformance; kitchen: KitchenReport };

export const DEFAULT_THRESHOLD = 15;
const THRESHOLDS = [10, 15, 20, 30, 45, 60];

export class PerformanceState extends ReportState<PerformanceQuery, PerformanceData> {
	override readonly tables = STATION_TABLES;
	// Kunci urutan sama dengan Laporan Dapur lama, supaya urutan yang sudah diingat pengguna tetap terpakai.
	readonly hourSort = new ListSort('dapur-jam', sortKeys(hourColumns(() => false)), () => void this.queryChanged(this.query));
	readonly orderSort = new ListSort('dapur-terlama', sortKeys(orderColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters([
		{ kind: 'select', key: 'stasiun', label: termText.station, options: [] },
		{ kind: 'select', key: 'ambang', label: stationText.lateMoreThan, options: THRESHOLDS.map((minutes) => ({ value: String(minutes), label: format(controlText.minutesCount, { count: minutes }) })), empty: String(DEFAULT_THRESHOLD) }
	]);

	get query(): PerformanceQuery {
		return {
			branch: this.filters.get('cabang'),
			range: this.filters.range('rentang'),
			station: this.filters.get('stasiun'),
			threshold: Number(this.filters.get('ambang'))
		};
	}

	protected async fetch(query: PerformanceQuery): Promise<PerformanceData> {
		const range = rangeParams(query.range);
		const [station, kitchen] = await Promise.all([
			api.stations.performance({ ...range, station_id: query.station }),
			api.reports.kitchen({ ...range, threshold_minutes: query.threshold, hour_sort: this.hourSort.param, order_sort: this.orderSort.param })
		]);
		this.filters.setOptions('stasiun', station.stations.map((entry) => ({ value: entry.id, label: entry.name })));
		return { start: station.start, end: station.end, station, kitchen };
	}
}
