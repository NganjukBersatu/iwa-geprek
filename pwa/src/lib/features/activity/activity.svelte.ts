import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { stamp, type WibStamp } from '$lib/format/datetime';
import type { IconName } from '$lib/theme/icons';
import { t } from '$lib/text/t';
import { durationLabel } from '$lib/format/labels';

export const ACTIVITY_PAGE_SIZE = 10;
const PAGE_LIMIT = 100;
const LATE_STATUS = 'telat';
const AUTO_STATUS = 'auto';
const SICK_TYPE = 'sakit';
const APPROVED_STATUS = 'disetujui';

/** Penyaring jenis aktivitas; [key] adalah nilai yang dipahami server, null berarti semua. */
export const ACTIVITY_GROUPS = [
	{ key: null, label: 'activity_group_all' },
	{ key: 'attendance', label: 'activity_group_attendance' },
	{ key: 'task', label: 'activity_group_task' },
	{ key: 'overtime', label: 'activity_group_overtime' },
	{ key: 'leave', label: 'activity_group_leave' },
	{ key: 'operations', label: 'activity_group_operations' }
] as const;
export type ActivityGroup = (typeof ACTIVITY_GROUPS)[number];

export type ActivityEvent = {
	id: string;
	action: string;
	at: WibStamp;
	/** Judul tugas, nomor nota, kode shift, atau jenis izin, tergantung aktivitasnya. */
	subject: string | null;
	/** Status kehadiran, keputusan izin, atau "auto" untuk absen pulang otomatis. */
	status: string | null;
	minutes: number | null;
};

type ActivityResponse = { events?: { id: string; action: string; at: string; subject?: string | null; status?: string | null; minutes?: number | null }[] };

const KNOWN_ACTIONS = ['clock_in', 'clock_out', 'task_done', 'overtime_recorded', 'leave_requested', 'leave_decided', 'order_created', 'order_voided', 'cash_opened', 'cash_closed'];

/** Aktivitas dengan jenis atau waktu yang tidak dikenal dilewati, bukan menggagalkan seluruh daftar. */
function eventsOf(response: ActivityResponse): ActivityEvent[] {
	return (response.events ?? []).flatMap((dto) => {
		const at = stamp(dto.at);
		return KNOWN_ACTIONS.includes(dto.action) && at ? [{ id: dto.id, action: dto.action, at, subject: dto.subject ?? null, status: dto.status ?? null, minutes: dto.minutes ?? null }] : [];
	});
}

export function eventTitle(event: ActivityEvent): string {
	switch (event.action) {
		case 'clock_in':
			return t('activity_clock_in');
		case 'clock_out':
			return t('activity_clock_out');
		case 'task_done':
			return t('activity_task_done');
		case 'overtime_recorded':
			return t('activity_overtime');
		case 'leave_requested':
			return event.subject === SICK_TYPE ? t('activity_leave_sick') : t('activity_leave_permit');
		case 'leave_decided':
			return t('activity_leave_decided');
		case 'order_created':
			return t('activity_order_created');
		case 'order_voided':
			return t('activity_order_voided');
		case 'cash_opened':
			return t('activity_cash_opened');
		default:
			return t('activity_cash_closed');
	}
}

export function eventDetail(event: ActivityEvent): string | null {
	switch (event.action) {
		case 'clock_in':
			return event.status === LATE_STATUS ? t('activity_late') : null;
		case 'clock_out':
			return event.status === AUTO_STATUS ? t('activity_auto_closed') : null;
		case 'overtime_recorded':
			return event.minutes !== null ? durationLabel(event.minutes) : null;
		case 'leave_requested':
			return t('activity_leave_pending');
		case 'leave_decided':
			return event.status === APPROVED_STATUS ? t('activity_leave_approved') : t('activity_leave_rejected');
		default:
			return event.subject;
	}
}

export function eventIcon(event: ActivityEvent): IconName {
	switch (event.action) {
		case 'clock_in':
		case 'clock_out':
			return 'CalendarCheck';
		case 'task_done':
			return 'Checklist';
		case 'overtime_recorded':
			return 'Moon';
		case 'leave_requested':
		case 'leave_decided':
			return 'Briefcase';
		case 'order_created':
		case 'order_voided':
			return 'Cart';
		default:
			return 'Cash';
	}
}

/** Keadaan halaman Riwayat: penyaring jenis, lalu daftar aktivitas karyawan dari semua perangkat. */
export class ActivityState {
	group = $state.raw<ActivityGroup>(ACTIVITY_GROUPS[0]);
	events = $state<ActivityEvent[]>([]);
	/** Halaman daftar, berbasis nol. */
	page = $state(0);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);

	private token = 0;

	constructor(private readonly onSessionExpired: () => void) {}

	get pageCount(): number {
		return Math.ceil(this.events.length / ACTIVITY_PAGE_SIZE);
	}

	get pageEvents(): ActivityEvent[] {
		const page = Math.min(this.page, Math.max(this.pageCount - 1, 0));
		return this.events.slice(page * ACTIVITY_PAGE_SIZE, (page + 1) * ACTIVITY_PAGE_SIZE);
	}

	select(group: ActivityGroup): void {
		if (group !== this.group) void this.load(group);
	}

	retry(): void {
		void this.load(this.group);
	}

	setPage(page: number): void {
		this.page = Math.min(Math.max(page, 0), Math.max(this.pageCount - 1, 0));
	}

	async load(group: ActivityGroup = this.group): Promise<void> {
		const token = ++this.token;
		this.group = group;
		this.events = [];
		this.page = 0;
		this.loading = true;
		this.failure = null;
		const result = await current.api().read<ActivityResponse>('/v2/activity', { limit: PAGE_LIMIT, group: group.key });
		if (token !== this.token) return;
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'success') this.events = eventsOf(result.value);
		else this.failure = result.failure;
	}
}
