import type { PromoUsage } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatNumber, formatRupiah } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { promoReportText } from '$lib/text/promo-report';

export const promoUsageColumns: Column<PromoUsage>[] = [
	{ key: 'nama', label: termText.promo, value: (row) => row.name, sort: 'name' },
	{ key: 'transaksi', label: termText.transaction, value: (row) => formatNumber(row.transactions, 0), sort: 'transactions' },
	{ key: 'potongan', label: promoReportText.totalDiscount, value: (row) => formatRupiah(row.total_discount), class: () => 'font-semibold', sort: 'discount' },
	{ key: 'rata', label: promoReportText.averagePerTransaction, value: (row) => formatRupiah(row.average_discount), sort: 'average' },
	{ key: 'bersih', label: promoReportText.netRevenue, value: (row) => formatRupiah(row.net_revenue), sort: 'net_revenue' }
];
