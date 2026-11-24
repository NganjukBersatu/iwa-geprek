import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { DailyOverview } from '$lib/api/types';
import { formatMonthYear, formatRange, type DateRange } from '$lib/date/range';
import { rangeParams, type ReportQuery } from '../report/report.svelte';
import { DepositsState } from '../deposits/deposits.svelte';
import { createFinanceFilters } from './filters';
import { QcState } from './qc.svelte';
import { TransactionsState } from './transactions.svelte';
import { financeText } from '$lib/text/finance';

export type OverviewQuery = ReportQuery;

export class OverviewState {
	filters = createFinanceFilters();
	qc = new QcState(this.filters);
	transactions = new TransactionsState(this.filters);
	deposits = new DepositsState(this.filters);

	loading = $state(true);
	error = $state('');
	data = $state<DailyOverview | null>(null);

	private token = 0;

	get query(): OverviewQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	get range(): DateRange | null {
		return this.query.range ?? (this.data ? { from: this.data.start, to: this.data.end } : null);
	}

	/** One row per day of the range, oldest first, as the server lists them. */
	get rows() {
		return this.data?.rows ?? [];
	}

	/** The rows of the table: all of them, or only those the Setoran filter keeps. */
	get tableRows() {
		return this.deposits.filter ? this.rows.filter((row) => this.deposits.keeps(row.date)) : this.rows;
	}

	get periodLabel(): string {
		const range = this.range;
		return range ? formatRange(range) : 'periode bawaan';
	}

	get tableTitle(): string {
		const range = this.range;
		if (!range) return '';
		return range.from.slice(0, 7) === range.to.slice(0, 7) ? formatMonthYear(range.from).toUpperCase() : this.periodLabel.toUpperCase();
	}

	get tableKey(): string {
		return [this.transactions.key, this.qc.status].join('|');
	}

	setBranches(options: { value: string; label: string }[]): void {
		this.filters.setOptions('cabang', options);
	}

	reloadTables(): void {
		this.transactions.reloadIfChanged();
		this.qc.reloadIfChanged();
	}

	private loadDependents(range: DateRange, quiet: boolean): void {
		if (!quiet) this.transactions.page = 1;
		void this.transactions.load(range, quiet);
		void this.qc.load(range, quiet);
		void this.deposits.load(range, quiet);
	}

	/** Reloads without dimming or clearing: what the screen shows stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(this.query, true);
	}

	async load(query: OverviewQuery = this.query, quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		if (!quiet) this.error = '';

		if (query.range) this.loadDependents(query.range, quiet);

		try {
			const data = await api.reports.dailyOverview(rangeParams(query.range));
			if (token !== this.token) return;
			this.data = data;
			if (!query.range) this.loadDependents({ from: data.start, to: data.end }, quiet);
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.data = null;
			this.error = userMessage(error, financeText.overviewLoadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
