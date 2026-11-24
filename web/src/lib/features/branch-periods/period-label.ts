import type { BranchPeriod } from '$lib/api/types';
import { formatDayMonth, formatMonthYear } from '$lib/date/range';
import { branchPeriodText } from '$lib/text/branch-periods';
import { format } from '$lib/text/format';

/** Periode dinamai menurut bulan tanggal akhirnya, ditemani rentangnya supaya dua periode di bulan yang sama tetap bisa dibedakan. */
export function periodLabel(period: BranchPeriod): string {
	return format(branchPeriodText.periodRange, { month: formatMonthYear(period.end), from: formatDayMonth(period.start), to: formatDayMonth(period.end) });
}
