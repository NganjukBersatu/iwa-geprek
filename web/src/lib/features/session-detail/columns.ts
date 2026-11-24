import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { Expense, SessionOrder } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
import { formatTime } from '$lib/format/datetime';
import { FUND_SOURCES } from '../finance/fund-sources';
import { termText } from '$lib/text/terms';
import { sessionDetailText } from '$lib/text/session-detail';

export const sessionOrderColumns: Column<SessionOrder>[] = [
	{ key: 'pelanggan', label: termText.customer, align: 'left', value: (order) => order.customer_name ?? termText.unnamed, sort: 'customer' },
	{ key: 'waktu', label: termText.time, align: 'left', value: (order) => formatTime(order.created_at), sort: 'created_at' },
	{ key: 'metode', label: termText.method, align: 'left', value: (order) => order.payment_method_label ?? EMPTY_VALUE, sort: 'method' },
	{ key: 'total', label: termText.total, value: (order) => formatRupiah(order.total), class: (order) => (order.voided ? `${QUIET_VALUE} line-through` : ''), sort: 'total' }
];

export const sessionExpenseColumns: Column<Expense>[] = [
	{ key: 'barang', label: termText.remark, align: 'left', value: (item) => item.item_name, sort: 'item' },
	{ key: 'waktu', label: termText.time, align: 'left', value: (item) => formatTime(item.created_at), sort: 'created_at' },
	{ key: 'sumber', label: sessionDetailText.fundingSource, align: 'left', value: (item) => FUND_SOURCES[item.fund_source] ?? item.fund_source, sort: 'fund_source' },
	{ key: 'jumlah', label: termText.quantity, value: (item) => formatRupiah(item.amount), sort: 'amount' }
];
