import type { Overpayment } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { actionText } from '$lib/text/actions';
import { overpaymentText } from '$lib/text/overpayments';

export const statusLabel = (row: Overpayment): string => (row.voided ? actionText.cancel : overpaymentText.valid);

/** The branch column only when every branch is shown; the same columns feed the table and the download. */
export function overpaymentColumns(allBranches: boolean): Column<Overpayment>[] {
	return [
		{ key: 'nota', label: overpaymentText.receipt, align: 'left', value: (row) => row.receipt_number ?? EMPTY_VALUE, sort: 'receipt' },
		...(allBranches ? [{ key: 'cabang', label: termText.branch, align: 'left' as const, value: (row: Overpayment) => row.outlet_name, sort: 'outlet' }] : []),
		{ key: 'waktu', label: termText.time, align: 'left', value: (row) => formatDateTime(row.recorded_at), sort: 'recorded_at' },
		{ key: 'kasir', label: termText.cashier, align: 'left', value: (row) => row.cashier, sort: 'cashier' },
		{ key: 'metode', label: termText.method, align: 'left', value: (row) => row.method_label, sort: 'method' },
		{ key: 'status', label: termText.status, align: 'left', value: statusLabel, sort: 'voided' },
		{ key: 'total', label: overpaymentText.orderTotal, value: (row) => formatRupiah(row.order_total), sort: 'order_total' },
		{ key: 'diterima', label: overpaymentText.received, value: (row) => formatRupiah(row.received), sort: 'received' },
		{ key: 'kelebihan', label: overpaymentText.excess, value: (row) => formatRupiah(row.amount), class: () => 'font-semibold text-warning-700', sort: 'amount' }
	];
}
