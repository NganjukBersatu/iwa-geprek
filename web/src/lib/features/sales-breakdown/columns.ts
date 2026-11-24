import type { BreakdownRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatNumber, formatPercentPlain, formatRupiah, formatRupiahOrDash } from '$lib/format/currency';
import { salesBreakdownText } from '$lib/text/sales-breakdown';
import { termText } from '$lib/text/terms';

const common = (name: string): Column<BreakdownRow>[] => [
	{ key: 'nama', label: name, align: 'left', value: (row) => row.label, sort: 'name' },
	{ key: 'struk', label: salesBreakdownText.receipts, value: (row) => formatNumber(row.transaction_count, 0), sort: 'transactions' },
	{ key: 'omzet', label: termText.revenue, value: (row) => formatRupiah(row.sales_total), class: () => 'font-semibold', sort: 'sales' },
	{ key: 'rata_rata', label: salesBreakdownText.averagePerReceipt, value: (row) => formatRupiah(row.average_per_transaction), sort: 'average' }
];

const share: Column<BreakdownRow> = { key: 'persen', label: '%', value: (row) => formatPercentPlain(row.sales_percent), class: () => 'text-slate-500' };

export const orderTypeColumns: Column<BreakdownRow>[] = [...common(salesBreakdownText.orderType), share];

export const outletColumns: Column<BreakdownRow>[] = [
	...common(termText.branch),
	{ key: 'laba_kotor', label: salesBreakdownText.grossProfit, value: (row) => formatRupiahOrDash(row.gross_profit), sort: 'profit' },
	share
];
