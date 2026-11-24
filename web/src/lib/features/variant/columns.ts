import type { ExtraRow, VariantRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatNumber, formatPercentPlain, formatRupiah, formatRupiahOrDash } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { variantReportText } from '$lib/text/variant-report';

export function variantColumns(byMenu: boolean): Column<VariantRow>[] {
	return [
		{ key: 'pilihan', label: byMenu ? variantReportText.choiceOrMenu : variantReportText.choice, align: 'left', value: (row) => row.option, sort: 'option' },
		{ key: 'porsi', label: variantReportText.servings, value: (row) => formatNumber(row.portions, 0), class: () => 'font-semibold', sort: 'portions' },
		{ key: 'persen', label: variantReportText.servingsPercent, align: 'left', value: (row) => formatPercentPlain(row.portions_percent) },
		{ key: 'omzet', label: variantReportText.lineRevenue, value: (row) => formatRupiah(row.revenue), sort: 'revenue' },
		{ key: 'margin', label: variantReportText.margin, value: (row) => formatRupiahOrDash(row.margin), sort: 'margin' }
	];
}

export const extraColumns: Column<ExtraRow>[] = [
	{ key: 'ekstra', label: termText.extra, align: 'left', value: (row) => row.extra, sort: 'extra' },
	{ key: 'jumlah', label: variantReportText.sold, value: (row) => formatNumber(row.quantity, 0), class: () => 'font-semibold', sort: 'quantity' },
	{ key: 'transaksi', label: termText.transaction, value: (row) => formatNumber(row.transactions, 0), sort: 'transactions' },
	{ key: 'pendapatan', label: variantReportText.revenue, value: (row) => formatRupiahOrDash(row.revenue), sort: 'revenue' },
	{ key: 'persen', label: variantReportText.revenuePercent, align: 'left', value: (row) => formatPercentPlain(row.revenue_percent) },
	{ key: 'laba', label: variantReportText.profit, value: (row) => formatRupiahOrDash(row.profit), sort: 'profit' }
];
