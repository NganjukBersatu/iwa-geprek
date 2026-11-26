import { api } from '$lib/api';
import type { Cancellation } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ManageState } from '../manage/manage.svelte';

export class CancellationsState extends ManageState<Cancellation> {
	override readonly tables = ['cancellation_requests', 'orders'];
	/** Only those who may decide see the requests; the server refuses everyone else. */
	get canDecide(): boolean {
		return access.allows('decide_cancellations');
	}

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
}
