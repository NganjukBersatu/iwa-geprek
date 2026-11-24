import { controlText } from '$lib/text/controls';
import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { NonCashCheckRow, TransactionRow } from '$lib/api/types';
import { BRANCH_SORT } from '$lib/components/table/branch-column';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatAmount, formatMillions, formatRupiah, formatSigned } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { actionText } from '$lib/text/actions';
import { financeText } from '$lib/text/finance';
import { format } from '$lib/text/format';

const place = (row: TransactionRow) => [row.table_no ? format(controlText.tableNumberLabel, { number: row.table_no }) : '', row.customer_name ?? ''].filter(Boolean).join(' · ') || EMPTY_VALUE;

export const transactionColumns: Column<TransactionRow>[] = [
	{ key: 'waktu', label: termText.time, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'created_at' },
	{ key: 'nota', label: financeText.receiptNumber, align: 'left', value: (row) => row.receipt_number ?? row.id.slice(0, 8).toUpperCase(), class: () => 'font-medium', sort: 'receipt' },
	{ key: 'kasir', label: termText.cashier, align: 'left', value: (row) => row.cashier, sort: 'cashier' },
	{ key: 'tempat', label: financeText.tableOrCustomer, align: 'left', value: place, sort: 'place' },
	{ key: 'metode', label: termText.method, align: 'left', value: (row) => row.method_label, sort: 'method' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.voided ? actionText.cancel : financeText.valid), class: (row) => (row.voided ? 'font-medium text-danger-700' : 'text-slate-500'), sort: 'voided' },
	{ key: 'total', label: termText.total, value: (row) => formatRupiah(row.total), class: (row) => `font-semibold ${row.voided ? 'text-danger-700 line-through' : ''}`, sort: 'total' }
];

const statusInk = (status: string) => (status === 'mismatch' ? 'text-danger-700' : status === 'balanced' ? 'text-success-700' : QUIET_VALUE);

/** The last column is the difference in millions, so only Selisih offers that order. */
export function qcColumns(allBranches: boolean, methods: string): Column<NonCashCheckRow>[] {
	return [
		{ key: 'tanggal', label: termText.date, align: 'left', value: (row) => row.date, sort: 'date' },
		...(allBranches ? [{ key: 'cabang', label: termText.branch, align: 'left' as const, value: (row: NonCashCheckRow) => row.outlet_name, sort: BRANCH_SORT }] : []),
		{ key: 'sistem', label: financeText.systemNonCash, value: (row) => formatAmount(row.recorded), sort: 'recorded' },
		{ key: 'nominal', label: `Nominal Non-tunai${methods}`, value: (row) => (row.bank_amount === null ? EMPTY_VALUE : formatAmount(row.bank_amount)), sort: 'bank_amount' },
		{ key: 'selisih', label: termText.difference, value: (row) => (row.difference === null ? EMPTY_VALUE : formatSigned(row.difference)), class: (row) => `font-semibold ${statusInk(row.status)}`, sort: 'difference' },
		{ key: 'balance', label: financeText.differenceMillions, value: (row) => (row.difference === null ? EMPTY_VALUE : formatMillions(row.difference)), class: (row) => `font-semibold ${statusInk(row.status)}` }
	];
}
