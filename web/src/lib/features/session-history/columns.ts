import type { SessionHistoryRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatRupiah, formatSigned } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { sessionHistoryText } from '$lib/text/session-history';

export const sessionHistoryColumns: Column<SessionHistoryRow>[] = [
	{ key: 'kasir', label: termText.cashier, align: 'left', value: (row) => row.cashier_username, sort: 'cashier' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet_name ?? EMPTY_VALUE, sort: 'outlet' },
	{ key: 'dibuka', label: sessionHistoryText.opened, align: 'left', value: (row) => formatDateTime(row.opened_at), sort: 'opened_at' },
	{ key: 'ditutup', label: termText.closed, align: 'left', value: (row) => (row.closed_at ? formatDateTime(row.closed_at) : EMPTY_VALUE), sort: 'closed_at' },
	{ key: 'pendapatan', label: sessionHistoryText.revenue, value: (row) => formatRupiah(row.revenue), sort: 'revenue' },
	{ key: 'pengeluaran', label: termText.expense, value: (row) => formatRupiah(row.expenses), sort: 'expenses' },
	{
		key: 'selisih',
		label: termText.difference,
		value: (row) => (row.difference === null ? EMPTY_VALUE : formatSigned(row.difference)),
		class: (row) => (row.difference !== null && Number(row.difference) < 0 ? 'font-semibold text-danger-700' : ''),
		sort: 'difference'
	}
];
