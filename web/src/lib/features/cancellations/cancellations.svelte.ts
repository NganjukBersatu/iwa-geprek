import { api } from '$lib/api';
import type { Cancellation } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { DayWarning } from '../deposits/day-warning.svelte';
import { ManageState } from '../manage/manage.svelte';
import { cancellationText } from '$lib/text/cancellations';

export class CancellationsState extends ManageState<Cancellation> {
	override readonly tables = ['cancellation_requests', 'orders'];
	/** Only those who may decide see the requests; the server refuses everyone else. */
	get canDecide(): boolean {
		return access.allows('decide_cancellations');
	}

	/** The request whose approval waits for a confirmation, since an approval cancels the order for good. */
	approving = $state<Cancellation | null>(null);
	busyId = $state<string | null>(null);
	/** The request whose details are open; the decision is made from there, not from the row. */
	opened = $state<Cancellation | null>(null);
	readonly warning = new DayWarning();

	protected async fetch(): Promise<void> {
		if (!this.canDecide) return;
		const page = await api.cancellations.list({ page: this.page, size: pageSize.value });
		if (page.items.length === 0 && page.total > 0 && this.page > 1) {
			this.page = Math.ceil(page.total / pageSize.value);
			return this.fetch();
		}
		this.items = page.items;
		this.total = page.total;
	}

	protected label(request: Cancellation): string {
		return request.receipt_number ?? request.order_id;
	}

	open(request: Cancellation): void {
		this.actionError = '';
		this.opened = request;
	}

	closeDetail(): void {
		this.opened = null;
		this.actionError = '';
	}

	askApprove(request: Cancellation): void {
		this.actionError = '';
		this.approving = request;
		void this.warning.read([{ outlet_id: request.outlet_id, day: request.order_business_day }]);
	}

	closeDialogs(): void {
		this.approving = null;
		this.actionError = '';
		this.warning.clear();
	}

	async confirmApprove(): Promise<void> {
		const request = this.approving;
		if (!request) return;
		if (await this.decide(request, true)) {
			this.approving = null;
			this.opened = null;
		}
	}

	async reject(request: Cancellation): Promise<void> {
		if (await this.decide(request, false)) this.opened = null;
	}

	private async decide(request: Cancellation, approve: boolean): Promise<boolean> {
		this.busyId = request.id;
		const done = await this.attempt(() => api.cancellations.decide(request.id, { approve }), cancellationText.decisionFailed);
		this.busyId = null;
		if (done) await this.refresh();
		return done;
	}
}
