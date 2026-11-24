import type { BranchPeriod } from '$lib/api/types';
import type { Tone } from '$lib/components/card/tone';
import type { Column } from '$lib/components/table/types';
import { formatDate, formatMonthYear } from '$lib/date/range';
import { branchPeriodText as text } from '$lib/text/branch-periods';

export type PeriodRow = BranchPeriod & { id: string };

/** Asal tanggal sebuah periode: patokan pola dari form cabang, digeser satu bulan saja, atau dibentuk dari pola. */
export function periodSource(period: BranchPeriod): { label: string; tone: Tone } {
	if (period.sets_pattern) return { label: text.sourcePattern, tone: 'brand' };
	if (period.adjusted) return { label: text.sourceShifted, tone: 'info' };
	return { label: text.sourceFollowing, tone: 'neutral' };
}

export const periodColumns: Column<PeriodRow>[] = [
	{ key: 'period', label: text.columns.period, align: 'left', value: (row) => formatMonthYear(row.end) },
	{ key: 'start', label: text.columns.start, align: 'left', value: (row) => formatDate(row.start) },
	{ key: 'end', label: text.columns.end, align: 'left', value: (row) => formatDate(row.end) },
	{ key: 'source', label: text.columns.source, align: 'left', value: (row) => periodSource(row).label },
	{ key: 'status', label: text.columns.status, align: 'left', value: (row) => (row.running ? text.running : text.past) }
];
