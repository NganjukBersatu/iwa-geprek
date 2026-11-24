import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { MoneyChangePage } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { moneyChangeColumns } from './columns';
import { moneyChangeText } from '$lib/text/money-changes';

/** The money trail of one session, deleted transactions and expenses included. */
export class SessionChangesState {
	data = $state<MoneyChangePage | null>(null);
	loading = $state(false);
	error = $state('');
	page = $state(1);
	private token = 0;
	readonly sort = new ListSort('jejak-uang-sesi', sortKeys(moneyChangeColumns(false)), () => {
		this.page = 1;
		void this.load();
	});

	constructor(readonly sessionId: string) {}

	setPage(page: number): void {
		this.page = page;
		void this.load();
	}

	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		try {
			const data = await api.moneyChanges.ofSession(this.sessionId, this.page, pageSize.value, this.sort.param);
			if (token !== this.token) return;
			this.data = data;
			this.error = '';
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.error = userMessage(error, moneyChangeText.loadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
