/** Format tanggal dan jam kehadiran; seluruh jam ditampilkan dalam WIB (UTC+7). */
const WIB_OFFSET_MINUTES = 7 * 60;
const WIB_ZONE = '+07:00';
const SECONDS_PER_DAY = 86_400;

export type WibStamp = { date: string; time: string };
export type YearMonth = { year: number; month: number };

const two = (value: number): string => String(value).padStart(2, '0');

export const previousMonth = (month: YearMonth): YearMonth => (month.month === 1 ? { year: month.year - 1, month: 12 } : { year: month.year, month: month.month - 1 });
export const nextMonth = (month: YearMonth): YearMonth => (month.month === 12 ? { year: month.year + 1, month: 1 } : { year: month.year, month: month.month + 1 });
export const sameMonth = (a: YearMonth, b: YearMonth): boolean => a.year === b.year && a.month === b.month;

function isLeap(year: number): boolean {
	return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
}

export function daysInMonth(month: YearMonth): number {
	if (month.month === 2) return isLeap(month.year) ? 29 : 28;
	return [4, 6, 9, 11].includes(month.month) ? 30 : 31;
}

export const dateOf = (month: YearMonth, day: number): string => `${month.year}-${two(month.month)}-${two(day)}`;
export const firstDay = (month: YearMonth): string => dateOf(month, 1);
export const lastDay = (month: YearMonth): string => dateOf(month, daysInMonth(month));
/** Bulan dalam bentuk YYYY-MM, seperti yang diminta rute rekap. */
export const monthKey = (month: YearMonth): string => `${month.year}-${two(month.month)}`;
/** Bulan dari tanggal "YYYY-MM-DD". */
export const monthOf = (date: string): YearMonth => ({ year: Number(date.slice(0, 4)), month: Number(date.slice(5, 7)) });

/** Indeks hari (0 = Minggu) dari tanggal "YYYY-MM-DD". */
export function weekdayIndex(date: string): number {
	const [year = 0, month = 1, day = 1] = date.slice(0, 10).split('-').map(Number);
	return new Date(Date.UTC(year, month - 1, day)).getUTCDay();
}

export const dayOfMonth = (date: string): string => date.slice(8, 10).replace(/^0+/, '');
export const monthIndex = (date: string): number => Number(date.slice(5, 7)) - 1;

/** Jam "HH:MM" dari menit sejak tengah malam. */
export const clockOf = (minuteOfDay: number): string => `${two(Math.floor(minuteOfDay / 60))}:${two(minuteOfDay % 60)}`;

/** Tanggal dan jam WIB dari detik sejak epoch. */
export function stampAt(epochSeconds: number): WibStamp {
	const shifted = new Date((epochSeconds + WIB_OFFSET_MINUTES * 60) * 1000);
	return {
		date: `${shifted.getUTCFullYear()}-${two(shifted.getUTCMonth() + 1)}-${two(shifted.getUTCDate())}`,
		time: `${two(shifted.getUTCHours())}:${two(shifted.getUTCMinutes())}`
	};
}

const ISO = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(Z|[+-]\d{2}(?::?\d{2})?)?/;

/** Detik sejak epoch dari stempel ISO; tanpa zona dianggap UTC seperti yang disimpan server. */
export function epochOf(iso: string | null | undefined): number | null {
	const match = iso ? ISO.exec(iso) : null;
	if (!match) return null;
	const [, year, month, day, hour, minute, second, zone] = match;
	let offset = 0;
	if (zone && zone !== 'Z') {
		const sign = zone.startsWith('-') ? -1 : 1;
		const digits = zone.slice(1).replace(':', '');
		offset = sign * (Number(digits.slice(0, 2)) * 60 + Number(digits.slice(2, 4) || 0));
	}
	const utc = Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute), Number(second ?? 0));
	return Math.floor(utc / 1000) - offset * 60;
}

/** Tanggal dan jam WIB dari stempel waktu ISO. */
export function stamp(iso: string | null | undefined): WibStamp | null {
	const epoch = epochOf(iso);
	return epoch === null ? null : stampAt(epoch);
}

export const clock = (iso: string | null | undefined): string | null => stamp(iso)?.time ?? null;

/** Tanggal hari ini menurut WIB, "YYYY-MM-DD", dari jam server. */
export const todayWib = (now: number): string => stampAt(now).date;
export const daysAgo = (now: number, days: number): string => stampAt(now - days * SECONDS_PER_DAY).date;

/** Stempel ISO 8601 berzona WIB dari tanggal "YYYY-MM-DD" dan jam "HH:MM", untuk dikirim ke server. */
export const wibIso = (date: string, time: string): string => `${date}T${time}:00${WIB_ZONE}`;

/** Selisih menit dua jam "HH:MM"; selesai yang tidak lebih besar dari mulai berarti lewat tengah malam. */
export function spanMinutes(start: string, end: string): number {
	const from = Number(start.slice(0, 2)) * 60 + Number(start.slice(3, 5));
	const to = Number(end.slice(0, 2)) * 60 + Number(end.slice(3, 5));
	return to > from ? to - from : to + 1440 - from;
}

/** Jam dan menit (menit dua digit) untuk diisikan ke format durasi. */
export const durationParts = (totalMinutes: number): [string, string] => [String(Math.floor(totalMinutes / 60)), two(totalMinutes % 60)];

export const minutesOfDay = (time: string): number => Number(time.slice(0, 2)) * 60 + Number(time.slice(3, 5));
