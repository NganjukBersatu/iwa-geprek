import type { BusyProductRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
import { productPeakText } from '$lib/text/product-peak';

const count = (value: number) => formatNumber(value, 0);
const percent = () => 'text-slate-500';

export function productPeakColumns(unitName: string): Column<BusyProductRow>[] {
	return [
		{ key: 'produk', label: productPeakText.product, align: 'left', value: (row) => row.menu_item_name },
		{ key: 'label', label: unitName, align: 'left', value: (row) => row.label, class: percent },
		{ key: 'qty', label: productPeakText.productCount, value: (row) => count(row.qty), class: () => 'font-semibold' },
		{ key: 'qty_persen', label: productPeakText.productPercent, value: (row) => formatPercentPlain(row.qty_percent), class: percent },
		{ key: 'transaksi', label: productPeakText.transactionCount, value: (row) => count(row.transactions) },
		{ key: 'transaksi_persen', label: productPeakText.transactionPercent, value: (row) => formatPercentPlain(row.transactions_percent), class: percent },
		{ key: 'omzet', label: productPeakText.salesRupiah, value: (row) => formatRupiah(row.revenue), class: () => 'font-semibold' },
		{ key: 'omzet_persen', label: productPeakText.salesPercent, value: (row) => formatPercentPlain(row.revenue_percent), class: percent }
	];
}
