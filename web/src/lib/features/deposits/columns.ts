import type { Deposit, DepositDay } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { dayLabel } from '$lib/date/range';
import { formatRupiah } from '$lib/format/currency';
import { STATUS_LABEL } from './format';
import { termText } from '$lib/text/terms';
import { depositText } from '$lib/text/deposits';

type Share = Deposit['days'][number];

const dayName = (iso: string) => {
	const label = dayLabel(iso);
	return `${label.weekday} ${label.day}`;
};

export const dayColumns: Column<DepositDay>[] = [
	{ key: 'tanggal', label: termText.date, align: 'left', value: (row) => dayName(row.day), sort: 'day' },
	{ key: 'wajib', label: depositText.dueToDeposit, value: (row) => formatRupiah(row.due), sort: 'due' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => STATUS_LABEL[row.status], sort: 'status' },
	{ key: 'disetor', label: depositText.deposited, value: (row) => formatRupiah(row.paid), sort: 'paid' },
	{ key: 'sisa', label: termText.remaining, value: (row) => formatRupiah(row.left), class: () => 'font-semibold', sort: 'left' }
];

/** The day's status comes from the list of days, so this table orders by date and amount only. */
export function shareColumns(dayOf: (day: string) => DepositDay | undefined): Column<Share>[] {
	return [
		{ key: 'tanggal', label: termText.date, align: 'left', value: (row) => dayName(row.day), sort: 'day' },
		{ key: 'status', label: depositText.dayStatus, align: 'left', value: (row) => STATUS_LABEL[dayOf(row.day)?.status ?? 'belum'] },
		{ key: 'dialokasikan', label: depositText.allocated, value: (row) => formatRupiah(row.amount), class: () => 'font-semibold', sort: 'amount' }
	];
}
