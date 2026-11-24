import type { AttendanceDto, AttendanceStateDto, BranchDto, ScheduleSummaryDto } from '$lib/api/types';
import { stamp, type WibStamp } from '$lib/format/datetime';
import type { LocationFix } from '$lib/platform/location';

export type ClockKind = 'in' | 'out';

/** Penugasan yang berlaku untuk karyawan, dengan jam mulai dan selesai nyata; [id] dikirim saat absen datang. */
export type ScheduleSummary = { id: string | null; code: string | null; colorHex: string | null; startsAt: WibStamp | null; endsAt: WibStamp | null };

export type AttendanceRecord = {
	late: boolean;
	clockIn: WibStamp | null;
	clockOut: WibStamp | null;
	autoClosed: boolean;
	photoInUrl: string | null;
	photoOutUrl: string | null;
	/** Jam kerja di dalam jam shift, dihitung backend. */
	workMinutes: number | null;
};

/** Absen yang ditutup sistem dan belum diberitahukan ke karyawan. */
export type AutoCloseNotice = { id: string; clockIn: WibStamp | null; clockOut: WibStamp | null };

export type ClockInBlockReason = 'not-open-yet' | 'already-used' | 'ended' | 'no-permission' | 'no-schedule';

/** Alasan absen datang belum bisa dilakukan; [at] jam dibukanya absen atau jam jadwal berakhir. */
export type ClockInBlock = { reason: ClockInBlockReason; schedule: ScheduleSummary | null; at: WibStamp | null };

/** Cabang patokan absen berikutnya; titik atau radius yang kosong berarti jarak tidak dinilai. */
export type AttendanceBranch = { name: string; latitude: number | null; longitude: number | null; radiusMeters: number | null };

export type AttendanceState = {
	canClockIn: boolean;
	canClockOut: boolean;
	record: AttendanceRecord | null;
	schedule: ScheduleSummary | null;
	notices: AutoCloseNotice[];
	clockInBlock: ClockInBlock | null;
	/** Tidak punya jadwal hari ini, jadi absen datang dimulai dengan absen mandiri. */
	canSelfSchedule: boolean;
	branch: AttendanceBranch | null;
};

/** Absen yang baru berhasil; [minutes] adalah jam datang (menit sejak 00.00) atau durasi kerja, null bila belum terbaca. */
export type ClockCelebration = { kind: ClockKind; minutes: number | null };

/** Isi satu absen: foto, posisi, keterangan bila di luar lokasi, dan [scheduleId] jadwal yang diabsen (hanya absen datang). */
export type ClockRequest = { scheduleId: string | null; photo: Blob; fix: LocationFix; outside: boolean; note: string | null };

const STATUS_LATE = 'telat';
const BLOCK_REASONS: Record<string, ClockInBlockReason> = { not_open_yet: 'not-open-yet', already_used: 'already-used', ended: 'ended', no_permission: 'no-permission' };

export function scheduleOf(dto: ScheduleSummaryDto | null | undefined): ScheduleSummary | null {
	if (!dto) return null;
	return { id: dto.id ?? null, code: dto.code, colorHex: dto.color, startsAt: stamp(dto.starts_at), endsAt: stamp(dto.ends_at) };
}

export function recordOf(dto: AttendanceDto | null | undefined): AttendanceRecord | null {
	if (!dto) return null;
	return {
		late: dto.status === STATUS_LATE,
		clockIn: stamp(dto.clock_in_at),
		clockOut: stamp(dto.clock_out_at),
		autoClosed: dto.auto_closed,
		photoInUrl: dto.clock_in_photo_url,
		photoOutUrl: dto.clock_out_photo_url,
		workMinutes: dto.work_minutes
	};
}

function branchOf(dto: BranchDto | null | undefined): AttendanceBranch | null {
	return dto ? { name: dto.name, latitude: dto.latitude, longitude: dto.longitude, radiusMeters: dto.radius_meters } : null;
}

export function stateOf(dto: AttendanceStateDto): AttendanceState {
	return {
		canClockIn: dto.can_clock_in,
		canClockOut: dto.can_clock_out,
		record: recordOf(dto.attendance),
		schedule: scheduleOf(dto.schedule),
		notices: dto.auto_close_notices.map((notice) => ({ id: notice.id, clockIn: stamp(notice.clock_in_at), clockOut: stamp(notice.clock_out_at) })),
		clockInBlock: dto.clock_in_block
			? { reason: BLOCK_REASONS[dto.clock_in_block.reason] ?? 'no-schedule', schedule: scheduleOf(dto.clock_in_block.schedule), at: stamp(dto.clock_in_block.at) }
			: null,
		canSelfSchedule: dto.can_self_schedule,
		branch: branchOf(dto.branch)
	};
}
