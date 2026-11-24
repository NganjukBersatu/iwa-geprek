import type { Schemas } from '$lib/api/contract';
import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { stamp, todayWib, type WibStamp, type YearMonth } from '$lib/format/datetime';
import { ServerClock } from '$lib/time/server-clock';
import { t } from '$lib/text/t';

export type ProfileInfo = { name: string; roleName: string; outletName: string | null; photoUrl: string | null };

/** Tugas pribadi diberikan ke satu orang; tugas outlet milik semua orang di outlet. */
export type PendingKind = 'personal' | 'routine' | 'outlet';
/** [caption] menggantikan batas waktu bila ada, misalnya rentang waktu tugas outlet. */
export type PendingTask = { title: string; due: WibStamp | null; kind: PendingKind; caption: string | null };

/** Ringkasan kehadiran bulan berjalan untuk kartu di dasbor. */
export type AttendanceMonth = { month: YearMonth; present: number; late: number; notPresent: number; workMinutes: number; overtimeMinutes: number; penalty: number };

type SummaryResponse = { month: string; totals?: Partial<Schemas['TotalsOut']> };
type ProfileResponse = { name?: string | null; username: string; role_name: string; outlet_name?: string | null; photo_url?: string | null };
type TaskResponse = { items?: { status: string; title: string; due_at?: string | null }[] };
type BatchResponse = { items?: { kind?: string; name: string; start_clock: string; end_clock: string; completed?: boolean }[] };
type ScheduleResponse = { role_name?: string | null }[];

function attendanceOf(dto: SummaryResponse): AttendanceMonth {
	const totals = dto.totals ?? {};
	const [year = 0, month = 1] = dto.month.split('-').map(Number);
	return {
		month: { year, month },
		present: (totals.present ?? 0) + (totals.late ?? 0),
		late: totals.late ?? 0,
		notPresent: (totals.leave ?? 0) + (totals.sick ?? 0) + (totals.absent ?? 0),
		workMinutes: totals.work_minutes ?? 0,
		overtimeMinutes: totals.overtime_minutes ?? 0,
		penalty: totals.penalty ?? 0
	};
}

/** Keadaan dashboard: identitas, penugasan hari ini, ringkasan kehadiran bulan ini, dan tugas yang menunggu. */
export class DashboardState {
	profile = $state<ProfileInfo | null>(null);
	loading = $state(true);
	attendance = $state<AttendanceMonth | null>(null);
	failure = $state<AppFailure | null>(null);
	/** Penugasan hari ini; null bila belum diketahui atau jadwal ada tetapi tanpa peran. */
	todayAssignment = $state<string | null>(null);
	pendingTasks = $state<PendingTask[]>([]);

	private token = 0;

	constructor(private readonly onSessionExpired: () => void) {}

	/** Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi. */
	async load(): Promise<void> {
		const token = ++this.token;
		this.loading = true;
		this.failure = null;
		const api = current.api();

		if (this.profile === null) {
			const result = await api.read<ProfileResponse>('/v2/profile');
			if (token !== this.token) return;
			if (result.kind === 'unauthorized') return this.onSessionExpired();
			if (result.kind === 'failure') return this.fail(result.failure);
			const dto = result.value;
			this.profile = { name: dto.name?.trim() || dto.username, roleName: dto.role_name, outletName: dto.outlet_name ?? null, photoUrl: dto.photo_url ?? null };
		}

		void this.loadAssignment(todayWib(ServerClock.nowEpochSeconds()));

		const summary = await api.read<SummaryResponse>('/v2/attendance/summary');
		if (token !== this.token) return;
		if (summary.kind === 'unauthorized') return this.onSessionExpired();
		if (summary.kind === 'failure') return this.fail(summary.failure);
		this.attendance = attendanceOf(summary.value);

		const [tasks, batches] = await Promise.all([api.read<TaskResponse>('/v2/tasks/mine', { size: 100 }), api.read<BatchResponse>('/v2/batches/today')]);
		if (token !== this.token) return;
		const taskItems = tasks.kind === 'success' ? (tasks.value.items ?? []) : [];
		const batchItems = batches.kind === 'success' ? (batches.value.items ?? []) : [];
		this.pendingTasks = [
			...taskItems.map((task): PendingTask => ({ title: task.title, due: stamp(task.due_at), kind: 'personal', caption: null })),
			...batchItems.filter((batch) => !batch.completed).map((batch): PendingTask => ({ title: batch.name, due: null, kind: batch.kind === 'routine' ? 'routine' : 'outlet', caption: `${batch.start_clock}–${batch.end_clock}` }))
		];
		this.loading = false;
	}

	/** Gagal memuat jadwal tidak menggagalkan dashboard; label penugasan hanya tidak tampil. */
	private async loadAssignment(date: string): Promise<void> {
		const result = await current.api().read<ScheduleResponse>('/v2/schedule/mine', { date });
		if (result.kind !== 'success') return;
		if (result.value.length === 0) {
			this.todayAssignment = t('dashboard_no_schedule');
			return;
		}
		const roles = [...new Set(result.value.map((entry) => entry.role_name).filter((name): name is string => Boolean(name)))];
		this.todayAssignment = roles.length > 0 ? roles.join(', ') : null;
	}

	private fail(failure: AppFailure): void {
		this.loading = false;
		this.failure = failure;
	}
}
