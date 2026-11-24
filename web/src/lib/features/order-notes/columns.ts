import { controlText } from '$lib/text/controls';
import type { OrderNote } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { orderNoteText } from '$lib/text/order-notes';
import { format } from '$lib/text/format';

export const orderNoteColumns: Column<OrderNote>[] = [
	{ key: 'catatan', label: termText.note, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet_name ?? termText.allBranches, sort: 'outlet' },
	{ key: 'dipakai', label: orderNoteText.inUse, value: (row) => (row.used_by_orders > 0 ? format(controlText.ordersCount, { count: formatNumber(row.used_by_orders, 0) }) : EMPTY_VALUE), sort: 'used' }
];
