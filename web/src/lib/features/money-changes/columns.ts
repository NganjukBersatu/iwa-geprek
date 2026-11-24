import type { MoneyChange } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDate } from '$lib/date/range';
import { EMPTY_VALUE, formatRupiah, formatSigned } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { ACTION_LABELS, fieldsText, SUBJECT_LABELS, SYSTEM_ACTOR } from './labels';
import { termText } from '$lib/text/terms';
import { moneyChangeText } from '$lib/text/money-changes';

/** The branch column only when every branch is shown; the same columns feed the table and the download. */
export function moneyChangeColumns(allBranches: boolean): Column<MoneyChange>[] {
	return [
		{ key: 'hari', label: termText.day, align: 'left', value: (row) => formatDate(row.business_day), sort: 'business_day' },
		{ key: 'data', label: moneyChangeText.data, align: 'left', value: (row) => [SUBJECT_LABELS[row.subject], row.subject_label].filter(Boolean).join(' · '), sort: 'subject' },
		{ key: 'perubahan', label: moneyChangeText.change, align: 'left', value: (row) => ACTION_LABELS[row.action], sort: 'action' },
		{ key: 'bagian', label: moneyChangeText.part, align: 'left', value: (row) => fieldsText(row.fields) || EMPTY_VALUE },
		...(allBranches ? [{ key: 'cabang', label: termText.branch, align: 'left' as const, value: (row: MoneyChange) => row.outlet_name ?? EMPTY_VALUE, sort: 'outlet' }] : []),
		{ key: 'sebelum', label: moneyChangeText.before, value: (row) => formatRupiah(row.amount_before), sort: 'amount_before' },
		{ key: 'sesudah', label: moneyChangeText.after, value: (row) => formatRupiah(row.amount_after), sort: 'amount_after' },
		{
			key: 'selisih',
			label: termText.difference,
			value: (row) => formatSigned(row.difference),
			class: (row) => (Number(row.difference) < 0 ? 'font-semibold text-danger-700' : Number(row.difference) > 0 ? 'font-semibold text-success-700' : ''),
			sort: 'difference'
		},
		{ key: 'oleh', label: termText.by, align: 'left', value: (row) => (row.by_system ? SYSTEM_ACTOR : row.user_name), sort: 'user' },
		{ key: 'waktu', label: termText.time, align: 'left', value: (row) => formatDateTime(row.changed_at), sort: 'changed_at' }
	];
}
