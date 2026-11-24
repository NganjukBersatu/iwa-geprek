import { controlText } from '$lib/text/controls';
import { api } from '$lib/api';
import type { TurnoverReport, TurnoverRow } from '$lib/api/types';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState, type ReportQuery } from '../report/report.svelte';
import { STOCK_TABLES } from '$lib/live/tables';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { turnoverColumns } from './columns';
import { turnoverText } from '$lib/text/turnover';
import { format } from '$lib/text/format';

export type TurnoverQuery = ReportQuery & { targetDays: number };

export const DEFAULT_TARGET = 14;

const groups = {
	beli: (row: TurnoverRow) => row.status === 'out' || row.status === 'urgent',
	tidur: (row: TurnoverRow) => row.status === 'dormant',
	lambat: (row: TurnoverRow) => row.status === 'slow'
} as const;

export class TurnoverState extends ReportState<TurnoverQuery, TurnoverReport> {
	override readonly tables = STOCK_TABLES;
	readonly sort = new ListSort('perputaran', sortKeys(turnoverColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters([
		{ kind: 'select', key: 'belanja', label: turnoverText.purchaseFor, options: [7, 14, 30, 60].map((days) => ({ value: String(days), label: format(controlText.daysCount, { count: days }) })), empty: String(DEFAULT_TARGET) },
		{
			kind: 'select',
			key: 'kelompok_stok',
			label: turnoverText.group,
			options: [
				{ value: 'beli', label: turnoverText.needsPurchaseLower },
				{ value: 'tidur', label: turnoverText.idle },
				{ value: 'lambat', label: turnoverText.slow }
			]
		},
	]);

	get query(): TurnoverQuery {
		return {
			branch: this.filters.get('cabang'),
			range: this.filters.range('rentang'),
			targetDays: Number(this.filters.get('belanja'))
		};
	}

	get toBuy(): number {
		return (this.data?.out_count ?? 0) + (this.data?.urgent_count ?? 0);
	}

	get matching(): TurnoverRow[] {
		const group = this.filters.get('kelompok_stok') as keyof typeof groups | null;
		const term = this.search.toLowerCase();
		return (this.data?.rows ?? [])
			.filter((row) => !group || groups[group](row))
			.filter((row) => !term || row.name.toLowerCase().includes(term) || (row.category ?? '').toLowerCase().includes(term));
	}

	protected override readonly paging = 'client';

	get pageRows(): TurnoverRow[] {
		return this.pageOf(this.matching).rows;
	}

	protected fetch(query: TurnoverQuery): Promise<TurnoverReport> {
		return api.reports.stockTurnover({ ...rangeParams(query.range), target_days: query.targetDays, sort: this.sort.param });
	}
}
