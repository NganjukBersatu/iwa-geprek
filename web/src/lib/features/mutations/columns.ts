import type { MutationRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatRupiah, formatSigned } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { mutationText } from '$lib/text/mutations';

export const mutationColumns: Column<MutationRow>[] = [
	{ key: 'sesi', label: mutationText.session, align: 'left', value: (row) => row.cashier_username, sort: 'cashier' },
	{ key: 'dibuka', label: mutationText.opened, align: 'left', value: (row) => formatDateTime(row.opened_at), sort: 'opened_at' },
	{ key: 'tunai', label: mutationText.cashRevenue, value: (row) => formatRupiah(row.cash_revenue), sort: 'cash_revenue' },
	{ key: 'nontunai', label: termText.nonCash, value: (row) => formatRupiah(row.non_cash_revenue), sort: 'non_cash_revenue' },
	{ key: 'belanja', label: termText.purchase, value: (row) => formatRupiah(row.spending), sort: 'spending' },
	{
		key: 'selisih',
		label: mutationText.revenueDifference,
		value: (row) => (row.revenue_difference === null ? termText.running : formatSigned(row.revenue_difference)),
		class: (row) => (row.revenue_difference !== null && Number(row.revenue_difference) < 0 ? 'font-semibold text-danger-700' : ''),
		sort: 'revenue_difference'
	}
];
