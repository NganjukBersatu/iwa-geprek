import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { PaymentGroup, TransactionReport } from '$lib/api/types';
import type { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { transactionColumns } from './columns';
import { financeText } from '$lib/text/finance';

export class TransactionsState {
	page = $state(1);
	focusDate = $state<string | null>(null);
	report = $state<TransactionReport | null>(null);
	loading = $state(false);
	error = $state('');

	private range: DateRange | null = null;
	private token = 0;
	private loadedKey = '';
	readonly sort = new ListSort('transaksi', sortKeys(transactionColumns), () => {
		this.page = 1;
		void this.load();
	});

	constructor(private filters: Filters) {}

	get group(): PaymentGroup {
		return (this.filters.get('kelompok_bayar') as PaymentGroup | null) ?? 'all';
	}

	get method(): string {
		return this.filters.get('metode') ?? '';
	}

	get includeCancelled(): boolean {
		return this.filters.get('batal') === 'ya';
	}

	get key(): string {
		return [this.group, this.method, this.includeCancelled, this.focusDate].join('|');
	}

	get methods() {
		return (this.report?.by_method ?? []).filter((method) =>
			this.group === 'cash' ? method.code === 'tunai' : this.group === 'non_cash' ? method.code !== 'tunai' : true
		);
	}

	setPage(page: number): void {
		this.page = page;
		void this.load();
	}

	focus(date: string | null): void {
		this.focusDate = date;
		this.filters.clear('metode');
		if (date) this.filters.set('kelompok_bayar', 'non_cash');
	}

	reloadIfChanged(): void {
		if (this.key === this.loadedKey) return;
		this.page = 1;
		void this.load();
	}

	async load(range: DateRange | null = this.range, quiet = false): Promise<void> {
		if (!range) return;
		this.range = range;
		this.loadedKey = this.key;
		const scope = this.focusDate ? { from: this.focusDate, to: this.focusDate } : range;
		const token = ++this.token;
		if (!quiet) this.loading = true;
		if (!quiet) this.error = '';
		try {
			const report = await api.reports.transactions({
				start: scope.from,
				end: scope.to,
				group: this.group,
				method: this.method || undefined,
				include_voided: this.includeCancelled,
				sort: this.sort.param,
				page: this.page,
				per_page: pageSize.value
			});
			if (token !== this.token) return;
			this.report = report;
			this.filters.setOptions(
				'metode',
				this.methods.map((method) => ({ value: method.code, label: `${method.label} (${method.count})` }))
			);
		} catch (error) {
			if (token === this.token && !quiet) this.error = userMessage(error, financeText.transactionsLoadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
