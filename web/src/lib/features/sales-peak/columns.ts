import type { BusySalesRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { salesPeakText } from '$lib/text/sales-peak';

const count = (value: number) => formatNumber(value, 0);
const percent = 'text-slate-500';

export function peakColumns(unitName: string): Column<BusySalesRow>[] {
	return [
		{ key: 'label', label: unitName, align: 'left', value: (row) => row.label, sort: 'time' },
		{ key: 'penjualan', label: salesPeakText.sales, value: (row) => formatRupiah(row.sales), class: () => 'font-semibold', sort: 'sales' },
		{ key: 'penjualan_persen', label: '%', value: (row) => formatPercentPlain(row.sales_percent), class: () => percent },
		{ key: 'transaksi', label: termText.transaction, value: (row) => count(row.transactions), sort: 'transactions' },
		{ key: 'transaksi_persen', label: '%', value: (row) => formatPercentPlain(row.transactions_percent), class: () => percent },
		{ key: 'produk', label: salesPeakText.product, value: (row) => count(row.products), sort: 'products' },
		{ key: 'produk_persen', label: '%', value: (row) => formatPercentPlain(row.products_percent), class: () => percent },
		{ key: 'produk_rata_harian', label: salesPeakText.dailyAverage, value: (row) => formatNumber(row.products_average, 1) }
	];
}
