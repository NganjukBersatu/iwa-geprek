import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { MarginItem } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatNumber, formatPercentOrDash, formatRupiahOrDash } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { marginText } from '$lib/text/margin';

const loss = (item: MarginItem) => item.margin !== null && Number(item.margin) < 0;

export const marginColumns: Column<MarginItem>[] = [
	{ key: 'menu', label: termText.menu, align: 'left', value: (row) => row.menu_item_name, sort: 'menu' },
	{ key: 'qty', label: marginText.sold, value: (row) => formatNumber(row.qty, 0), class: () => 'text-slate-500', sort: 'qty' },
	{ key: 'omzet', label: termText.revenue, value: (row) => formatRupiahOrDash(row.revenue), sort: 'revenue' },
	{ key: 'modal', label: marginText.cost, value: (row) => formatRupiahOrDash(row.cost), class: () => 'text-slate-500', sort: 'cost' },
	{
		key: 'laba',
		label: marginText.profit,
		value: (row) => formatRupiahOrDash(row.margin),
		class: (row) => `font-semibold ${row.margin === null ? QUIET_VALUE : loss(row) ? 'text-danger-700' : 'text-success-700'}`,
		sort: 'margin'
	},
	{ key: 'persen', label: '%', value: (row) => formatPercentOrDash(row.margin_percent), class: () => 'text-slate-500', sort: 'margin_percent' }
];
