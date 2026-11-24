import type { CodeGroup } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { formatClockRange, formatClockSpan } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { shiftCodeText } from '$lib/text/shift-codes';
import { format } from '$lib/text/format';

/** The same words the badge shows, for downloads where there is no badge. */
const hours = (start: string | null, end: string | null) => (start && end ? `${formatClockRange(start, end)} · ${formatClockSpan(start, end)}` : EMPTY_VALUE);

/** Codes whose name is used by more than one group, which legacy branches created on their own. */
export function twinCodes(groups: CodeGroup[]): Set<string> {
	const seen = new Map<string, number>();
	for (const group of groups) seen.set(group.code, (seen.get(group.code) ?? 0) + 1);
	return new Set([...seen].filter(([, count]) => count > 1).map(([code]) => code));
}

export const shiftCodeColumns: Column<CodeGroup>[] = [
	{ key: 'kode', label: termText.code, align: 'left', value: (row) => row.code, sort: 'code' },
	{ key: 'kategori', label: termText.category, align: 'left', value: (row) => row.category, sort: 'category' },
	{ key: 'jam', label: shiftCodeText.workHours, align: 'left', value: (row) => (row.is_day_off ? termText.dayOff : hours(row.start_clock, row.end_clock)), sort: 'hours' },
	{ key: 'lembur', label: shiftCodeText.overtime, align: 'left', value: (row) => hours(row.overtime_start_clock, row.overtime_end_clock), sort: 'overtime' },
	{ key: 'cabang', label: shiftCodeText.usedIn, align: 'left', value: (row) => row.branches.map((branch) => branch.name).join(', '), sort: 'branches' },
	{ key: 'jadwal', label: termText.schedule, value: (row) => (row.assignments > 0 ? format(shiftCodeText.assignmentsCount, { count: formatNumber(row.assignments, 0) }) : EMPTY_VALUE), sort: 'assignments' }
];
