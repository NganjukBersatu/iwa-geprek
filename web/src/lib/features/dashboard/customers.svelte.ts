import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { CustomerReport } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { customerText } from '$lib/text/customers';

/** The customers who came in the range, one page at a time, for the panel under the Pelanggan card. */
export class CustomersState {
	report = $state<CustomerReport | null>(null);
	loading = $state(false);
	error = $state('');
	page = $state(1);
	private token = 0;

	reset(): void {
		this.page = 1;
		this.report = null;
	}

	async load(range: DateRange, quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) {
			this.loading = true;
			this.error = '';
		}
		try {
			const report = await api.reports.customers({ start: range.from, end: range.to, page: this.page, size: pageSize.value });
			if (token === this.token) this.report = report;
		} catch (failure) {
			if (token !== this.token || quiet) return;
			this.report = null;
			this.error = userMessage(failure, customerText.loadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
