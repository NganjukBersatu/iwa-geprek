import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { Expense, SessionHistoryRow, SessionOrder } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { page } from '$app/state';
import { rememberedSearch, rememberSearch } from '$lib/components/filter/search';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { FUND_SOURCES } from '../finance/fund-sources';
import { sessionExpenseColumns, sessionOrderColumns } from './columns';
import { termText } from '$lib/text/terms';
import { sessionDetailText } from '$lib/text/session-detail';

const MAX_EXPENSES = 100;

export const ORDER_TYPE_LABELS: Record<string, string> = { free_table: sessionDetailText.dineIn, take_away: sessionDetailText.takeaway };

const matches = (query: string, parts: (string | null | undefined)[]): boolean => !query || parts.join(' ').toLowerCase().includes(query);

/** One cash session with its orders and expenses, each tab with its own filters under the one remembered search. */
export class SessionDetailState {
	row = $state<SessionHistoryRow | null>(null);
	orders = $state<SessionOrder[] | null>(null);
	/** Bill yang sudah dikerjakan dapur tetapi belum dibayar; kosong selama belum termuat atau gagal dimuat. */
	openBills = $state<SessionOrder[]>([]);
	expenses = $state<Expense[] | null>(null);
	loading = $state(true);
	error = $state('');
	ordersError = $state('');
	expensesError = $state('');
	tab = $state('orders');
	// Layar tempat daftar ini dibuat; pencariannya diingat untuk layar itu saja.
	readonly #searchPath = page.url.pathname;
	search = $state(rememberedSearch(this.#searchPath));
	readonly orderSort = new ListSort('sesi-transaksi', sortKeys(sessionOrderColumns), () => void this.refresh());
	readonly expenseSort = new ListSort('sesi-pengeluaran', sortKeys(sessionExpenseColumns), () => void this.refresh());

	orderFilters = new Filters([
		{ kind: 'select', key: 'metode', label: termText.method, options: [] },
		{ kind: 'select', key: 'jenis_pesanan', label: sessionDetailText.orderKind, options: Object.entries(ORDER_TYPE_LABELS).map(([value, label]) => ({ value, label })) }
	]);
	expenseFilters = new Filters([{ kind: 'select', key: 'sumber', label: sessionDetailText.fundingSource, options: Object.entries(FUND_SOURCES).map(([value, label]) => ({ value, label })) }]);

	private token = 0;

	constructor(readonly id: string) {}

	get filters(): Filters {
		return this.tab === 'orders' ? this.orderFilters : this.expenseFilters;
	}

	get visibleOrders(): SessionOrder[] {
		const query = this.search.trim().toLowerCase();
		const method = this.orderFilters.get('metode');
		const type = this.orderFilters.get('jenis_pesanan');
		return (this.orders ?? []).filter(
			(order) =>
				(!method || order.payment_method === method) &&
				(!type || order.order_type === type) &&
				matches(query, [order.customer_name ?? 'tanpa nama', order.table_no ? `meja ${order.table_no}` : '', order.receipt_number, order.payment_method_label, order.note, ...order.items.map((item) => item.name)])
		);
	}

	get visibleExpenses(): Expense[] {
		const query = this.search.trim().toLowerCase();
		const source = this.expenseFilters.get('sumber');
		return (this.expenses ?? []).filter((item) => (!source || item.fund_source === source) && matches(query, [item.item_name, item.note, item.buyer]));
	}

	setTab(tab: string): void {
		this.tab = tab;
	}

	setSearch(query: string): void {
		this.search = query;
		rememberSearch(this.#searchPath, query);
	}

	/** Reloads without dimming or clearing: what the screen shows stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		const [row, orders, expenses, bills] = await Promise.allSettled([
			api.sessions.historyDetail(this.id),
			api.sessions.orders(this.id, this.orderSort.param),
			api.expenses.list({ session_id: this.id, size: MAX_EXPENSES, sort: this.expenseSort.param }),
			api.sessions.openBills(this.id)
		]);
		if (token !== this.token) return;
		const reason = (result: PromiseRejectedResult, fallback: string) => (userMessage(result.reason, fallback));
		if (row.status === 'fulfilled') {
			this.row = row.value;
			this.error = '';
		} else if (!quiet) {
			this.row = null;
			this.error = reason(row, sessionDetailText.sessionLoadFailed);
		}
		if (orders.status === 'fulfilled') {
			this.orders = orders.value;
			this.ordersError = '';
			const methods = new Map(orders.value.flatMap((order) => (order.payment_method ? [[order.payment_method, order.payment_method_label ?? order.payment_method] as const] : [])));
			this.orderFilters.setOptions('metode', [...methods].map(([value, label]) => ({ value, label })));
		} else this.ordersError = reason(orders, sessionDetailText.ordersLoadFailed);
		if (expenses.status === 'fulfilled') {
			this.expenses = expenses.value.items;
			this.expensesError = '';
		} else this.expensesError = reason(expenses, sessionDetailText.expensesLoadFailed);
		// Panel bill hanya pelengkap: bila gagal dimuat, daftar terakhir dipertahankan dan halaman sesi tetap tampil.
		if (bills.status === 'fulfilled') this.openBills = bills.value;
		this.loading = false;
	}
}
