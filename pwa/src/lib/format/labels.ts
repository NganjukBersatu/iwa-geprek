import { t, tArray } from '../text/t';
import { clockOf, dayOfMonth, durationParts, monthIndex, weekdayIndex, type WibStamp } from './datetime';

/** Contoh: "2 j 05 m" dari 125 menit. */
export function durationLabel(totalMinutes: number): string {
	const [hours, minutes] = durationParts(totalMinutes);
	return t('format_duration', hours, minutes);
}

/** Contoh: "12 Oktober 2026" dari "2026-10-12". */
export function longDateLabel(date: string): string {
	return t('format_date_plain', dayOfMonth(date), tArray('months')[monthIndex(date)] ?? '', date.slice(0, 4));
}

/** Contoh: "Senin, 12 Oktober 2026". */
export function weekdayDateLabel(date: string): string {
	return t('format_date_long', tArray('weekdays_long')[weekdayIndex(date)] ?? '', dayOfMonth(date), tArray('months')[monthIndex(date)] ?? '', date.slice(0, 4));
}

/** Contoh: "Sen 12 Okt · 08:00". */
export function whenLabel(stamp: WibStamp): string {
	return t('format_when', tArray('weekdays_short')[weekdayIndex(stamp.date)] ?? '', dayOfMonth(stamp.date), tArray('months_short')[monthIndex(stamp.date)] ?? '', stamp.time);
}

export const timeRange = (start: string, end: string): string => t('format_time_range', start, end);

export function monthYearLabel(month: { year: number; month: number }): string {
	return t('format_month_year', tArray('months')[month.month - 1] ?? '', String(month.year));
}

export function formatRupiah(amount: number): string {
	const sign = amount < 0 ? '-' : '';
	const digits = String(Math.abs(Math.trunc(amount))).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
	return `${sign}Rp ${digits}`;
}

export { clockOf };
