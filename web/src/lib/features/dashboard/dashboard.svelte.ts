import { listText } from '$lib/text/lists';
import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { Ability, CashierReport, Comparison, ComparisonMode, InventoryValue, Period, ProfitLoss, Summary, TransactionRow, TrendPoint } from '$lib/api/types';
import type { ComparisonParams } from '$lib/api/reports';
import { access } from '$lib/auth/access.svelte';
import { formatRange, type DateRange } from '$lib/date/range';
import { collectPages } from '../manage/collect';
import { rangeParams } from '../report/report.svelte';
import { createDashboardFilters } from './filters';
import { SessionsState } from './sessions.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { cashierColumns } from './columns';
import { pageText } from '$lib/text/pages';
import { format } from '$lib/text/format';

export type PanelKey = 'income' | 'expense' | 'profit' | null;
/** Kartu yang membuka panel; dua kartu bisa membuka panel yang sama, tetapi hanya yang ditekan yang tampil terbuka. */
export type PanelCard = 'income' | 'expense' | 'profit' | 'average';

export type DashboardQuery = {
	branch: string | null;
	period: Period;
	range: DateRange | null;
	comparison: Pick<ComparisonParams, 'mode' | 'previous_start' | 'previous_end'>;
};

const PERIOD_LABELS: Record<Period, string> = {
	daily: '7 hari terakhir',
	weekly: '4 minggu terakhir',
	monthly: '8 bulan terakhir'
};

const UNIT_LABELS: Record<Period, string> = {
	daily: 'per hari',
	weekly: 'per minggu',
	monthly: 'per bulan'
};

const sum = <T>(items: T[], pick: (item: T) => number): number => items.reduce((total, item) => total + pick(item), 0);

export class DashboardState {
	filters = createDashboardFilters();
	sessions = new SessionsState();
	readonly cashierSort = new ListSort('dasbor-kasir', sortKeys(cashierColumns), () => void this.loadCashiers());

	loading = $state(true);
	error = $state('');
	panel = $state<PanelKey>(null);
	private panelCard = $state<PanelCard | null>(null);
	/** True once the first load has finished, whatever cards it brought; the skeleton page shows only before it. */
	loaded = $state(false);

	points = $state<TrendPoint[]>([]);
	unit = $state<Period>('daily');
	appliedRange = $state<DateRange | null>(null);
	summary = $state<Summary | null>(null);
	cashiers = $state<CashierReport | null>(null);
	profitLoss = $state<ProfitLoss | null>(null);
	comparison = $state<Comparison | null>(null);
	inventory = $state<InventoryValue | null>(null);
	inventoryFailed = $state(false);


	private token = 0;

	get query(): DashboardQuery {
		const period = (this.filters.get('periode') ?? 'daily') as Period;
		return {
			branch: this.filters.get('cabang'),
			period,
			range: this.filters.range('rentang'),
			comparison: this.comparisonQuery()
		};
	}

	private comparisonQuery(): DashboardQuery['comparison'] {
		const value = this.filters.pick('bandingkan');
		if (!value) return { mode: 'auto' };
		if (typeof value === 'string') return { mode: value as ComparisonMode };
		if ('preset' in value) return { mode: value.preset as ComparisonMode };
		return { mode: 'custom', previous_start: value.from, previous_end: value.to };
	}

	get chartRows() {
		return this.points.map((point) => ({
			label: point.label,
			income: Number(point.income),
			expense: Number(point.expense),
			orderCount: point.order_count,
			averageTransaction: Number(point.average_transaction)
		}));
	}

	get totalIncome(): number {
		return sum(this.chartRows, (row) => row.income);
	}

	get totalExpense(): number {
		return sum(this.chartRows, (row) => row.expense);
	}

	get totalProfit(): number {
		return this.totalIncome - this.totalExpense;
	}

	get totalOrderCount(): number {
		return sum(this.chartRows, (row) => row.orderCount);
	}

	get averageTransaction(): number {
		if (this.summary) return Number(this.summary.sales.average_transaction);
		return this.totalOrderCount ? Math.round(this.totalIncome / this.totalOrderCount) : 0;
	}

	/** Pengunjung adalah jumlah struk yang tidak dibatalkan; pelanggan yang tercatat adalah rincian di dalamnya. */
	/** Keterangan kartu menu: jumlah transaksi, ditambah yang dibatalkan hanya bila ada. */
	get salesCaption(): string {
		const sales = this.summary?.sales;
		if (!sales) return '';
		const count = String(sales.transaction_count);
		return sales.voided_count > 0 ? format(pageText.transactionsWithVoided, { count, voided: String(sales.voided_count) }) : format(pageText.transactionsCount, { count });
	}

		get visitors(): number {
		return this.summary?.sales.transaction_count ?? this.totalOrderCount;
	}

	get periodLabel(): string {
		const { range, period } = this.query;
		return range ? formatRange(range) : PERIOD_LABELS[period];
	}

	get unitLabel(): string {
		return UNIT_LABELS[this.unit];
	}

	togglePanel(panel: Exclude<PanelKey, null>, card: PanelCard = panel): void {
		const closing = this.panel === panel && this.panelCard === card;
		this.panel = closing ? null : panel;
		this.panelCard = closing ? null : card;
	}

	/** Kartu yang sedang membuka panel; panel yang ditutup dari tombol tutupnya tidak menyisakan kartu terbuka. */
	opens(card: PanelCard): boolean {
		return this.panel !== null && this.panelCard === card;
	}

	setBranches(options: { value: string; label: string }[]): void {
		this.filters.setOptions('cabang', options);
	}

	/** Reloads without dimming or clearing: what the screen shows stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(this.query, true);
	}

	/** Each card is read and shown only when the account may see the report behind it; the server refuses the rest anyway. */
	can(ability: Ability): boolean {
		return access.allows(ability);
	}

	async load(query: DashboardQuery, quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		if (!quiet) this.error = '';

		try {
			// The days covered come from a call that carries no figure, so a card whose report the account may not see never stops the others.
			const window = await api.reports.window({ period: query.period, ...rangeParams(query.range) });
			if (token !== this.token) return;
			this.unit = window.period;
			const range = { from: window.start, to: window.end };
			const dates = { start: range.from, end: range.to };
			if (this.can('view_trend')) {
				const trend = await api.reports.trend({ period: query.period, ...rangeParams(query.range) });
				if (token !== this.token) return;
				this.points = trend.points;
				if (trend.points.length === 0) {
					this.clearDetails();
					return;
				}
			} else {
				this.points = [];
			}
			if (this.appliedRange?.from !== range.from || this.appliedRange?.to !== range.to) this.appliedRange = range;
			const [summary, cashiers, profitLoss, comparison] = await Promise.all([
				this.can('view_summary') ? api.reports.summary(dates) : null,
				this.can('view_cashier_figures') ? api.reports.cashiers({ ...dates, sort: this.cashierSort.param }) : null,
				this.can('view_profit_loss') ? api.reports.profitLoss(dates).catch(() => null) : null,
				this.can('view_comparison') ? this.loadComparison(dates, query.comparison) : null,
				this.can('view_transaction_list') ? this.sessions.load(range, quiet) : this.sessions.clear()
			]);
			if (token !== this.token) return;
			this.summary = summary;
			this.cashiers = cashiers;
			this.profitLoss = profitLoss;
			this.comparison = comparison;
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.points = [];
			this.clearDetails();
			this.error = userMessage(error, listText.reportLoadFailed);
		} finally {
			if (token === this.token) {
				this.loading = false;
				this.loaded = true;
			}
		}
	}

	/** Only the cashier table is read again when its order changes. */
	private async loadCashiers(): Promise<void> {
		const range = this.appliedRange;
		if (!range) return;
		const token = this.token;
		try {
			const cashiers = await api.reports.cashiers({ start: range.from, end: range.to, sort: this.cashierSort.param });
			if (token === this.token) this.cashiers = cashiers;
		} catch (error) {
			if (token === this.token) this.error = userMessage(error, listText.reportLoadFailed);
		}
	}

	private async loadComparison(dates: { start: string; end: string }, comparison: DashboardQuery['comparison']): Promise<Comparison | null> {
		try {
			return await api.reports.comparison({ ...dates, ...comparison });
		} catch {
			return null;
		}
	}

	private clearDetails(): void {
		this.appliedRange = null;
		this.summary = null;
		this.cashiers = null;
		this.profitLoss = null;
		this.comparison = null;
		this.sessions.clear();
	}

	async loadStock(): Promise<void> {
		if (!this.can('view_inventory_value')) return;
		try {
			this.inventory = await api.reports.inventoryValue();
			this.inventoryFailed = false;
		} catch {
			this.inventoryFailed = true;
		}
	}

	async exportRows(): Promise<TransactionRow[]> {
		const range = this.appliedRange;
		if (!range) return [];
		return collectPages(async (page, size) => {
			const result = await api.reports.transactions({ start: range.from, end: range.to, include_voided: true, page, per_page: size });
			return { items: result.rows, total: result.count };
		});
	}
}
