const ZONE = 'Asia/Jakarta';

export function formatTime(iso: string): string {
	return new Intl.DateTimeFormat('id-ID', { hour: '2-digit', minute: '2-digit', timeZone: ZONE }).format(new Date(iso));
}

export function formatDuration(minutes: number | null): string {
	if (minutes === null) return '—';
	return `${Math.floor(minutes / 60)}j ${String(minutes % 60).padStart(2, '0')}m`;
}

export function formatDateTime(iso: string): string {
	return new Intl.DateTimeFormat('id-ID', {
		day: '2-digit',
		month: 'short',
		hour: '2-digit',
		minute: '2-digit',
		timeZone: ZONE
	}).format(new Date(iso));
}

const MINUTES_PER_HOUR = 60;
const MINUTES_PER_DAY = 24 * MINUTES_PER_HOUR;

function clockMinutes(clock: string): number {
	const [hour, minute] = clock.split(':').map(Number);
	return (hour ?? 0) * MINUTES_PER_HOUR + (minute ?? 0);
}

/** "08:00–17:00", or an empty string when either end is missing. */
export function formatClockRange(start: string | null | undefined, end: string | null | undefined): string {
	return start && end ? `${start}–${end}` : '';
}

/** "9 jam" or "8,5 jam"; a span that ends past midnight still counts forward. */
export function formatClockSpan(start: string, end: string): string {
	const minutes = (clockMinutes(end) - clockMinutes(start) + MINUTES_PER_DAY) % MINUTES_PER_DAY || MINUTES_PER_DAY;
	const hours = minutes / MINUTES_PER_HOUR;
	return `${hours.toLocaleString('id-ID', { maximumFractionDigits: 1 })} jam`;
}
