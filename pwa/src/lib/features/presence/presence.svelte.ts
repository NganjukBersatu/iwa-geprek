import type { SummaryDto } from '$lib/api/types';
import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { monthKey, nextMonth, previousMonth, sameMonth, type YearMonth } from '$lib/format/datetime';

export type AttendanceStatus = 'present' | 'late' | 'permit' | 'sick' | 'absent';
export const LOCATION_MODE_OUTSIDE = 'outside';

export type AttendanceDay = {
	date: string;
	status: AttendanceStatus;
	clockIn: string | null;
	clockOut: string | null;
	lateMinutes: number;
	shiftCode: string | null;
	roleName: string | null;
	workMinutes: number | null;
	penalty: number;
	outsideScheduleReason: string | null;
	note: string | null;
	photoInUrl: string | null;
	photoOutUrl: string | null;
	/** [LOCATION_MODE_OUTSIDE] berarti absen dilakukan di luar radius lokasi. */
	modeIn: string | null;
	locationNoteIn: string | null;
	distanceIn: number | null;
	modeOut: string | null;
	locationNoteOut: string | null;
	distanceOut: number | null;
	/** Akurasi GPS dan batas radius cabang (meter) saat absen. */
	accuracyIn: number | null;
	radiusIn: number | null;
	accuracyOut: number | null;
	radiusOut: number | null;
	autoClosed: boolean;
};

export type AttendanceMonth = { month: YearMonth; present: number; late: number; notPresent: number; penalty: number; days: AttendanceDay[] };

const STATUSES: Record<string, AttendanceStatus> = { hadir: 'present', telat: 'late', izin: 'permit', sakit: 'sick' };

function monthOf(dto: SummaryDto): AttendanceMonth {
	const [year = 0, month = 1] = dto.month.split('-').map(Number);
	const totals = dto.totals;
	return {
		month: { year, month },
		present: totals.present + totals.late,
		late: totals.late,
		notPresent: totals.leave + totals.sick + totals.absent,
		penalty: totals.penalty,
		days: dto.days
			.map(
				(day): AttendanceDay => ({
					date: day.date,
					status: STATUSES[day.status] ?? 'absent',
					clockIn: day.clock_in_at,
					clockOut: day.clock_out_at,
					lateMinutes: day.late_minutes,
					shiftCode: day.shift_code,
					roleName: day.role_name,
					workMinutes: day.work_minutes,
					penalty: day.penalty,
					outsideScheduleReason: day.outside_schedule_reason,
					note: day.note,
					photoInUrl: day.clock_in_photo_url,
					photoOutUrl: day.clock_out_photo_url,
					modeIn: day.clock_in_location?.mode ?? null,
					locationNoteIn: day.clock_in_location?.note ?? null,
					distanceIn: day.clock_in_location?.distance_meters ?? null,
					modeOut: day.clock_out_location?.mode ?? null,
					locationNoteOut: day.clock_out_location?.note ?? null,
					distanceOut: day.clock_out_location?.distance_meters ?? null,
					accuracyIn: day.clock_in_location?.accuracy_meters ?? null,
					radiusIn: day.clock_in_location?.radius_meters ?? null,
					accuracyOut: day.clock_out_location?.accuracy_meters ?? null,
					radiusOut: day.clock_out_location?.radius_meters ?? null,
					autoClosed: day.auto_closed
				})
			)
			.sort((a, b) => b.date.localeCompare(a.date))
	};
}

/** Keadaan halaman Kehadiran: ringkasan satu bulan beserta hari-hari tercatatnya. */
export class PresenceState {
	month = $state<YearMonth | null>(null);
	attendance = $state<AttendanceMonth | null>(null);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	canGoNext = $state(false);

	/** Bulan berjalan menurut server, diketahui dari pemuatan pertama tanpa parameter. */
	private currentMonth: YearMonth | null = null;
	private token = 0;

	constructor(private readonly onSessionExpired: () => void) {}

	retry(): void {
		void this.load(this.month);
	}

	previousMonth(): void {
		if (this.month) void this.load(previousMonth(this.month));
	}

	nextMonth(): void {
		if (this.month && this.canGoNext) void this.load(nextMonth(this.month));
	}

	async load(target: YearMonth | null): Promise<void> {
		const token = ++this.token;
		this.loading = true;
		this.failure = null;
		if (target) this.month = target;
		const result = await current.api().read<SummaryDto>('/v2/attendance/summary', { month: target ? monthKey(target) : null });
		if (token !== this.token) return;
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'failure') {
			this.failure = result.failure;
			return;
		}
		const loaded = monthOf(result.value);
		if (target === null) this.currentMonth = loaded.month;
		this.attendance = loaded;
		this.month = loaded.month;
		this.canGoNext = this.currentMonth !== null && !sameMonth(loaded.month, this.currentMonth);
	}
}
