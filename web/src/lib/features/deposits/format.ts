import { formatDayMonth, shiftDays, todayIso } from '$lib/date/range';
import type { DepositStatus } from '$lib/api/types';
import type { Tone } from '$lib/components/card/tone';
import { depositText } from '$lib/text/deposits';

export const STATUS_LABEL: Record<DepositStatus, string> = { belum: depositText.statusNone, sebagian: depositText.statusPartial, lunas: depositText.statusDone };
export const STATUS_TONE: Record<DepositStatus, Tone> = { belum: 'danger', sebagian: 'warning', lunas: 'success' };

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/** Days as short ranges, "17–21 Okt" or "30 Sep–2 Okt" across a month, so a gap in the dates is visible at a glance. */
export function rangesOf(days: string[]): string {
	const sorted = [...days].sort();
	const groups: string[][] = [];
	for (const day of sorted) {
		const last = groups.at(-1);
		if (last && shiftDays(last.at(-1)!, 1) === day) last.push(day);
		else groups.push([day]);
	}
	return groups
		.map((group) => {
			const first = group[0]!;
			const last = group.at(-1)!;
			if (first === last) return formatDayMonth(first);
			const [startDay, startMonth] = formatDayMonth(first).split(' ');
			const [endDay, endMonth] = formatDayMonth(last).split(' ');
			return startMonth === endMonth ? `${startDay}–${endDay} ${endMonth}` : `${formatDayMonth(first)}–${formatDayMonth(last)}`;
		})
		.join(', ');
}

/** How many days ago a date was, counted in WIB days. */
export function daysAgo(iso: string, today = todayIso()): number {
	return Math.round((Date.parse(`${today}T00:00:00Z`) - Date.parse(`${iso}T00:00:00Z`)) / MS_PER_DAY);
}
