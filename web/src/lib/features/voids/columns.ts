import type { VoidedOrder } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { voidText } from '$lib/text/voids';

export const voidOrderName = (row: VoidedOrder) => `${row.customer_name || termText.unnamed}${row.table_no ? ` · Meja ${row.table_no}` : ''}`;

export const voidColumns: Column<VoidedOrder>[] = [
	{ key: 'pesanan', label: termText.order, align: 'left', value: voidOrderName, sort: 'order' },
	{ key: 'alasan', label: voidText.reason, align: 'left', value: (row) => row.reason ?? EMPTY_VALUE, sort: 'reason' },
	{ key: 'batal', label: voidText.cancelled, align: 'left', value: (row) => formatDateTime(row.voided_at), sort: 'voided_at' },
	{ key: 'dibuat', label: voidText.created, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'created_at' },
	{ key: 'kasir', label: termText.cashier, align: 'left', value: (row) => row.cashier_username ?? EMPTY_VALUE, sort: 'cashier' },
	{ key: 'oleh', label: termText.by, align: 'left', value: (row) => row.voided_by ?? EMPTY_VALUE, sort: 'voided_by' },
	{ key: 'total', label: voidText.value, value: (row) => formatRupiah(row.total), class: () => 'font-semibold text-danger-700', sort: 'total' }
];
