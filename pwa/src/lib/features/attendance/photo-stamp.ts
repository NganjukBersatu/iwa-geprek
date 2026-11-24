import { dayOfMonth, monthIndex, stampAt } from '$lib/format/datetime';
import { ServerClock } from '$lib/time/server-clock';
import type { LocationFix } from '$lib/platform/location';
import { distanceMeters } from '$lib/platform/location';
import type { StampLine } from '$lib/platform/photo';
import { t, tArray } from '$lib/text/t';
import type { AttendanceBranch } from './models';

const COORDINATE_DIGITS = 6;

/** Koordinat dengan enam angka di belakang koma. */
function coordinate(value: number): string {
	return value.toFixed(COORDINATE_DIGITS);
}

/** Isi cap foto absen: jam, tanggal, nama, cabang, koordinat, jarak, dan lokasi absen. */
export function stampLines(userName: string, branch: AttendanceBranch | null, fix: LocationFix, outside: boolean, note: string | null): StampLine[] {
	const now = stampAt(ServerClock.nowEpochSeconds());
	const date = t('format_date_plain', dayOfMonth(now.date), tArray('months')[monthIndex(now.date)] ?? '', now.date.slice(0, 4));
	const lines: StampLine[] = [
		{ text: t('attendance_stamp_time', now.time), bold: true },
		{ text: t('attendance_stamp_date', date), bold: true },
		{ text: t('attendance_stamp_name', userName) },
		...(branch ? [{ text: t('attendance_stamp_branch', branch.name) }] : []),
		{ text: t('attendance_stamp_coordinates', coordinate(fix.latitude), coordinate(fix.longitude), String(Math.round(fix.accuracyMeters))) }
	];
	if (branch && branch.latitude !== null && branch.longitude !== null && branch.radiusMeters !== null) {
		const meters = Math.round(distanceMeters(fix, branch.latitude, branch.longitude));
		lines.push({ text: t('attendance_stamp_distance', String(meters), String(branch.radiusMeters)) });
	}
	lines.push(outside ? { text: t('attendance_stamp_outside', note ?? ''), bold: true } : { text: t('attendance_stamp_inside') });
	return lines;
}
