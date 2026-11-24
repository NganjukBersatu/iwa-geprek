import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { VisitorDay, VisitorGroup } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDayMonth } from '$lib/date/range';
import { formatNumber, formatPercentPlain } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { visitorText } from '$lib/text/visitor';

export const UNRECORDED = visitorText.notRecorded;

export const groupColumns: Column<VisitorGroup>[] = [
	{ key: 'label', label: visitorText.group, value: (row) => row.label, class: (row) => (row.label === UNRECORDED ? QUIET_VALUE : ''), sort: 'label' },
	{ key: 'transaksi', label: termText.transaction, value: (row) => formatNumber(row.transactions, 0), sort: 'transactions' },
	{ key: 'persen', label: '%', value: (row) => formatPercentPlain(row.percent) },
	{ key: 'omzet', label: termText.revenue, value: (row) => formatNumber(row.revenue, 0), sort: 'revenue' }
];

const FIXED_DAY_SORTS = ['date', 'transactions', 'revenue'];

/** Group columns follow the data, so a day column is sortable when it is a fixed one or a group named by its position. */
export const isDaySort = (key: string) => FIXED_DAY_SORTS.includes(key) || /^(gender|category)_\d{1,3}$/.test(key);

export function dayColumns(genders: string[], categories: string[]): Column<VisitorDay>[] {
	return [
		{ key: 'tanggal', label: termText.date, value: (row) => formatDayMonth(row.date), sort: 'date' },
		{ key: 'transaksi', label: termText.transaction, value: (row) => formatNumber(row.transactions, 0), class: () => 'font-semibold', sort: 'transactions' },
		{ key: 'omzet', label: termText.revenue, value: (row) => formatNumber(row.revenue, 0), sort: 'revenue' },
		...genders.map((label, index) => ({ key: `g:${label}`, label, value: (row: VisitorDay) => formatNumber(row.genders[label] ?? 0, 0), sort: `gender_${index}` })),
		...categories.map((label, index) => ({ key: `k:${label}`, label, value: (row: VisitorDay) => formatNumber(row.categories[label] ?? 0, 0), sort: `category_${index}` }))
	];
}
