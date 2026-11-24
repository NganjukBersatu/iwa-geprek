import { api } from '$lib/api';
import type { LeaveRequest, LeaveStatus } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ManageState } from '../manage/manage.svelte';
import { termText } from '$lib/text/terms';
import { leaveRequestText } from '$lib/text/leave-requests';

export type LeaveQuery = { search: string | null; status: string | null };

export const LEAVE_STATUS_LABELS: Record<LeaveStatus, string> = { menunggu: leaveRequestText.pending, disetujui: leaveRequestText.approved, ditolak: leaveRequestText.rejected };

const DEFAULT_STATUS: LeaveStatus = 'menunggu';
const ALL = 'all';

export class LeaveRequestsState extends ManageState<LeaveRequest> {
	override readonly tables = ['leave_requests'];

	readonly filters = new Filters(
		[
			{
				kind: 'select',
				key: 'status_izin',
				label: termText.status,
				options: [...Object.entries(LEAVE_STATUS_LABELS).map(([value, label]) => ({ value, label })), { value: ALL, label: leaveRequestText.all }],
				empty: DEFAULT_STATUS
			}
		]
	);

	removing = $state<LeaveRequest | null>(null);
	busyId = $state<string | null>(null);
	/** Requests still waiting for a decision, whatever the filter says; shown on the tab. */
	pending = $state(0);

	/** Called after a decision or a deletion, which change the attendance records listed next to this panel. */
	onchanged: () => void = () => {};

	get query(): LeaveQuery {
		return { search: this.search || null, status: this.filters.get('status_izin') };
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const page = await api.leaveRequests.list({
			status: query.status === ALL ? undefined : ((query.status as LeaveStatus | null) ?? undefined),
			search: query.search ?? undefined,
			page: this.page,
			size: pageSize.value
		});
		if (page.items.length === 0 && page.total > 0 && this.page > 1) {
			this.page = Math.ceil(page.total / pageSize.value);
			return this.fetch();
		}
		this.items = page.items;
		this.total = page.total;
		this.pending = query.status === 'menunggu' ? page.total : (await api.leaveRequests.list({ status: 'menunggu', size: 1 })).total;
	}

	protected label(request: LeaveRequest): string {
		return request.name || request.username;
	}

	async decide(request: LeaveRequest, approve: boolean): Promise<void> {
		this.busyId = request.id;
		const done = await this.attempt(() => api.leaveRequests.decide(request.id, { approve }), leaveRequestText.decisionFailed);
		this.busyId = null;
		if (done) {
			await this.load();
			this.onchanged();
		} else this.error = this.actionError;
	}

	askRemove(request: LeaveRequest): void {
		this.actionError = '';
		this.removing = request;
	}

	closeDialogs(): void {
		this.removing = null;
		this.actionError = '';
	}

	async confirmRemove(): Promise<void> {
		const request = this.removing;
		if (!request) return;
		const done = await this.attempt(() => api.leaveRequests.remove(request.id), leaveRequestText.removeFailed);
		if (!done) return;
		this.removing = null;
		await this.load();
		this.onchanged();
	}
}
