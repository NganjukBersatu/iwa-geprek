import { DateFormatter, parseAbsolute, parseDate, toCalendarDate } from '@internationalized/date';
import { WIB_ZONE } from './zone';

const MIN_YEAR = 2000;
const MAX_YEAR = 2100;
const CENTURY = 2000;

const ISO = /^(\d{4})-(\d{1,2})-(\d{1,2})$/;
const DAY_FIRST = /^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2}|\d{4})$/;
const MONTH_NAME = /^(\d{1,2})[\s/.-]+([a-z]+)\.?[\s/.,-]+(\d{2}|\d{4})$/;
const INSTANT = /^\d{4}-\d{2}-\d{2}[t ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(z|[+-]\d{2}:?\d{2})$/;
const WALL_CLOCK_SUFFIX = /[t\s]\d{1,2}:\d{2}(:\d{2})?(\.\d+)?$/;

/** Month names come from the platform in both languages, so no table is kept by hand; a few spellings people use are added. */
const MONTH_BY_NAME = new Map<string, number>([['agt', 8], ['sept', 9]]);
for (const locale of ['id-ID', 'en-US']) {
	for (const month of ['short', 'long'] as const) {
		const names = new DateFormatter(locale, { month, timeZone: 'UTC' });
		for (let index = 1; index <= 12; index++) MONTH_BY_NAME.set(names.format(new Date(Date.UTC(2026, index - 1, 1))).toLowerCase().replace('.', ''), index);
	}
}

const written = new DateFormatter('id-ID', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' });

export type ParsedDay = { ok: true; iso: string } | { ok: false; message: string };

const fail = (text: string): ParsedDay => ({ ok: false, message: `Tanggal "${text.trim()}" tidak terbaca. Tulis 1/10/2026 atau 1 Okt 2026.` });

function checked(year: number, month: number, day: number): ParsedDay | null {
	if (year < MIN_YEAR || year > MAX_YEAR) return null;
	try {
		return { ok: true, iso: parseDate(`${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`).toString() };
	} catch {
		return null;
	}
}

const fullYear = (text: string) => (text.length === 2 ? CENTURY + Number(text) : Number(text));

function instantDay(text: string): ParsedDay | null {
	try {
		const day = toCalendarDate(parseAbsolute(text.replace(' ', 'T').toUpperCase(), WIB_ZONE));
		return checked(day.year, day.month, day.day);
	} catch {
		return null;
	}
}

/** The one reader of a typed or imported calendar day in WIB: ISO, day-first with / - . or a month name, never month-first, and an instant with a zone is turned into its WIB day; the answer is always YYYY-MM-DD. */
export function parseDay(text: string): ParsedDay {
	const cleaned = text.trim().toLowerCase().replace(/\s+/g, ' ');
	if (INSTANT.test(cleaned)) return instantDay(cleaned) ?? fail(text);
	const dated = cleaned.replace(WALL_CLOCK_SUFFIX, '');
	let found: ParsedDay | null = null;
	let match: RegExpMatchArray | null;
	if ((match = ISO.exec(dated))) found = checked(Number(match[1]), Number(match[2]), Number(match[3]));
	else if ((match = DAY_FIRST.exec(dated))) found = checked(fullYear(match[3]!), Number(match[2]), Number(match[1]));
	else if ((match = MONTH_NAME.exec(dated))) {
		const month = MONTH_BY_NAME.get(match[2]!);
		found = month ? checked(fullYear(match[3]!), month, Number(match[1])) : null;
	}
	return found ?? fail(text);
}

/** A stored day as people type it, 01/10/2026. */
export function dayText(iso: string): string {
	return written.format(parseDate(iso).toDate('UTC'));
}
