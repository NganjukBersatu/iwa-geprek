import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { failureText } from '$lib/failure/failure';
import { longDateLabel } from '$lib/format/labels';
import type { BadgeTone } from '$lib/components/feedback/types';
import { t } from '$lib/text/t';

const REQUESTS = '/v2/leave/requests';

export type LeaveType = 'izin' | 'sakit';
export type LeaveStatus = 'pending' | 'approved' | 'rejected';

export type LeaveRequest = {
	id: string;
	type: LeaveType;
	/** Tanggal "YYYY-MM-DD". */
	startDate: string;
	endDate: string;
	reason: string;
	status: LeaveStatus;
	decidedBy: string | null;
	managerNote: string | null;
	attachmentUrl: string | null;
	attachmentLink: string | null;
};

/** Lampiran pengajuan, foto JPEG atau PDF, beserta jenis dan nama berkas yang dikirim ke server. */
export type LeaveAttachment = { blob: Blob; fileName: string };

/** Isian pengajuan; [link] boleh kosong bila ada lampiran. */
export type LeaveForm = { type: LeaveType; startDate: string; endDate: string; reason: string; link: string };

type LeaveResponse = {
	id: string;
	type: string;
	start_date: string;
	end_date: string;
	reason: string;
	status: string;
	decided_by?: string | null;
	manager_note?: string | null;
	attachment_url?: string | null;
	attachment_link?: string | null;
};

const STATUSES: Record<string, LeaveStatus> = { disetujui: 'approved', ditolak: 'rejected' };

const requestOf = (dto: LeaveResponse): LeaveRequest => ({
	id: dto.id,
	type: dto.type === 'sakit' ? 'sakit' : 'izin',
	startDate: dto.start_date,
	endDate: dto.end_date,
	reason: dto.reason,
	status: STATUSES[dto.status] ?? 'pending',
	decidedBy: dto.decided_by ?? null,
	managerNote: dto.manager_note?.trim() ? dto.manager_note : null,
	attachmentUrl: dto.attachment_url ?? null,
	attachmentLink: dto.attachment_link?.trim() ? dto.attachment_link : null
});

export const leaveStatusTone = (status: LeaveStatus): BadgeTone => (status === 'approved' ? 'positive' : status === 'rejected' ? 'danger' : 'warning');
export const leaveTypeLabel = (type: LeaveType): string => (type === 'sakit' ? t('leave_type_sick') : t('leave_type_permit'));
export const leaveStatusLabel = (status: LeaveStatus): string => (status === 'approved' ? t('leave_status_approved') : status === 'rejected' ? t('leave_status_rejected') : t('leave_status_pending'));

/** Contoh: "12 Oktober 2026" untuk satu hari, "12 Oktober 2026 – 14 Oktober 2026" untuk rentang. */
export function leaveRangeLabel(request: LeaveRequest): string {
	const start = longDateLabel(request.startDate);
	return request.startDate === request.endDate ? start : t('leave_date_range', start, longDateLabel(request.endDate));
}

/** Keadaan bagian pengajuan izin: daftar milik sendiri, dan pengiriman atau pembatalan yang sedang berjalan. */
export class LeaveState {
	items = $state<LeaveRequest[]>([]);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	/** Sedang mengirim atau membatalkan pengajuan. */
	working = $state(false);
	error = $state<string | null>(null);

	constructor(private readonly onSessionExpired: () => void) {}

	async load(): Promise<void> {
		this.loading = this.items.length === 0;
		this.failure = null;
		const result = await current.api().read<LeaveResponse[]>(`${REQUESTS}/mine`);
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'success') this.items = result.value.map(requestOf);
		else this.failure = result.failure;
	}

	async submit(form: LeaveForm, attachment: LeaveAttachment | null): Promise<boolean> {
		const body = new FormData();
		body.append('type', form.type);
		body.append('start_date', form.startDate);
		body.append('end_date', form.endDate);
		body.append('reason', form.reason.trim());
		const link = form.link.trim();
		if (link && !attachment) body.append('link', link);
		if (attachment) body.append('file', attachment.blob, attachment.fileName);
		return this.run(() => current.api().write('POST', REQUESTS, body));
	}

	async cancel(id: string): Promise<boolean> {
		return this.run(() => current.api().write('DELETE', `${REQUESTS}/${id}`));
	}

	clearError(): void {
		this.error = null;
	}

	private async run(send: () => Promise<{ kind: 'success' | 'unauthorized' | 'failure'; failure?: AppFailure }>): Promise<boolean> {
		if (this.working) return false;
		this.working = true;
		this.error = null;
		const result = await send();
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return false;
		}
		this.working = false;
		if (result.kind === 'failure' && result.failure) {
			this.error = failureText(result.failure);
			return false;
		}
		void this.load();
		return true;
	}
}
