import { endOfMonth, fromDate, getDayOfWeek, parseDate, startOfMonth, toCalendarDate } from '@internationalized/date';
import { ServerClock } from '$lib/time/server-clock';
import { WIB_ZONE } from './zone';

export type DateRange = { from: string; to: string };

export type DatePreset = { value: string; label: string };

/** How far a range may reach: 'past' stops at today, since what has not happened has no figures; 'future' also reaches ahead, for plans such as schedules. */
export type DateReach = 'past' | 'future';

/** The last day a range of this reach may pick; null when it is open ahead. */
export function lastPickable(reach: DateReach): string | null {
	return reach === 'past' ? todayIso() : null;
}

const WEEK_STARTS_MONDAY = 'en-GB';

export const DATE_PRESETS: DatePreset[] = [
	{ value: 'today', label: 'Hari ini' },
	{ value: 'yesterday', label: 'Kemarin' },
	{ value: 'last7', label: '7 hari terakhir' },
	{ value: 'lastweek', label: 'Minggu lalu' },
	{ value: 'month', label: 'Bulan ini' }
];

export const WEEK_PRESETS: DatePreset[] = [
	{ value: 'week', label: 'Minggu ini' },
	{ value: 'nextweek', label: 'Minggu depan' },
	{ value: 'month_full', label: 'Seluruh bulan ini' }
];

export const LAST_30_PRESET: DatePreset = { value: 'last30', label: '30 hari terakhir' };

export function todayIso(now = ServerClock.now()): string {
	return toCalendarDate(fromDate(now, WIB_ZONE)).toString();
}

export function shiftDays(iso: string, days: number): string {
	return parseDate(iso).add({ days }).toString();
}

/** The Monday of the week that holds the given day. */
export function mondayOf(iso: string): string {
	const day = parseDate(iso);
	return day.subtract({ days: getDayOfWeek(day, WEEK_STARTS_MONDAY) }).toString();
}

export function presetRange(preset: string, today = todayIso()): DateRange | null {
	switch (preset) {
		case 'today':
			return { from: today, to: today };
		case 'yesterday':
			return { from: shiftDays(today, -1), to: shiftDays(today, -1) };
		case 'last7':
			return { from: shiftDays(today, -6), to: today };
		case 'last30':
			return { from: shiftDays(today, -29), to: today };
		case 'lastweek': {
			const from = shiftDays(mondayOf(today), -7);
			return { from, to: shiftDays(from, 6) };
		}
		case 'month':
				return { from: startOfMonth(parseDate(today)).toString(), to: today };
		case 'week': {
			const from = mondayOf(today);
			return { from, to: shiftDays(from, 6) };
		}
		case 'nextweek': {
			const from = shiftDays(mondayOf(today), 7);
			return { from, to: shiftDays(from, 6) };
		}
		case 'month_full': {
			const month = parseDate(today);
				return { from: startOfMonth(month).toString(), to: endOfMonth(month).toString() };
		}
		default:
			return null;
	}
}

export function formatDate(iso: string): string {
	return new Intl.DateTimeFormat('id-ID', {
		day: 'numeric',
		month: 'short',
		year: 'numeric',
		timeZone: 'UTC'
	}).format(new Date(`${iso}T00:00:00Z`));
}

export function formatRange(range: DateRange): string {
	return range.from === range.to
		? formatDate(range.from)
		: `${formatDate(range.from)} sampai ${formatDate(range.to)}`;
}

export function formatDayMonth(iso: string): string {
	return new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', timeZone: 'UTC' }).format(new Date(`${iso}T00:00:00Z`));
}

export function formatMonthYear(iso: string): string {
	return new Intl.DateTimeFormat('id-ID', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${iso}T00:00:00Z`));
}

export function dayLabel(iso: string): { weekday: string; day: number; sunday: boolean } {
	const date = new Date(`${iso}T00:00:00Z`);
	return {
		weekday: new Intl.DateTimeFormat('id-ID', { weekday: 'short', timeZone: 'UTC' }).format(date),
		day: date.getUTCDate(),
		sunday: date.getUTCDay() === 0
	};
}
