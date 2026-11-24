import type { CashierRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatRupiah } from '$lib/format/currency';
import { formatTime } from '$lib/format/datetime';
import type { SessionRow } from './sessions.svelte';
import { termText } from '$lib/text/terms';
import { dashboardCardText } from '$lib/text/dashboard-cards';

export type SessionKind = 'income' | 'expense' | 'profit';

const NOT_CLOSED = 'belum tutup shift';

export const sessionValue = (kind: SessionKind, row: SessionRow): number => (kind === 'income' ? row.income : kind === 'expense' ? row.expense : row.income - row.expense);

const VALUE_SORT: Record<SessionKind, string> = { income: 'revenue', expense: 'expenses', profit: 'profit' };
const VALUE_LABEL: Record<SessionKind, string> = { income: termText.income, expense: termText.expense, profit: termText.profit };

const range = (row: SessionRow) => `${formatTime(row.start)} - ${row.end ? formatTime(row.end) : 'berjalan'}`;

export function sessionColumns(kind: SessionKind): Column<SessionRow>[] {
	return [
		{ key: 'kasir', label: termText.cashier, align: 'left', value: (row) => row.cashier, sort: 'cashier' },
		{ key: 'jam', label: dashboardCardText.sessionHours, align: 'left', value: range, sort: 'opened_at' },
		{
			key: 'nilai',
			label: VALUE_LABEL[kind],
			value: (row) => formatRupiah(sessionValue(kind, row)),
			class: (row) => `font-semibold ${kind === 'expense' || (kind === 'profit' && sessionValue(kind, row) < 0) ? 'text-danger-700' : 'text-slate-800'}`,
			sort: VALUE_SORT[kind]
		}
	];
}

/** Every key the sessions panel can be ordered by, whichever value it shows. */
export const SESSION_SORTS = ['cashier', 'opened_at', ...Object.values(VALUE_SORT)];

function diffClass(value: number): string {
	if (value < 0) return 'text-danger-700';
	return value > 0 ? 'text-warning-700' : 'text-slate-500';
}

function diffText(row: CashierRow): string {
	if (row.session_count === 0) return NOT_CLOSED;
	const value = Number(row.difference_total);
	return `${value > 0 ? '+' : ''}${formatRupiah(value)}`;
}

export const cashierColumns: Column<CashierRow>[] = [
	{ key: 'kasir', label: termText.cashier, align: 'left', value: (row) => row.username, sort: 'cashier' },
	{ key: 'transaksi', label: termText.transaction, value: (row) => String(row.transaction_count), sort: 'transactions' },
	{ key: 'penjualan', label: dashboardCardText.sales, value: (row) => formatRupiah(row.sales_total), sort: 'sales' },
	{ key: 'pengeluaran', label: termText.expense, value: (row) => formatRupiah(row.expense_total), sort: 'expenses' },
	{
		key: 'selisih',
		label: dashboardCardText.cashDifference,
		value: diffText,
		class: (row) => (row.session_count === 0 ? 'text-slate-500' : `font-semibold ${diffClass(Number(row.difference_total))}`),
		sort: 'difference'
	}
];
