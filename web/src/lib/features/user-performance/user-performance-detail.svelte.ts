import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { PerformanceRange } from '$lib/api/userPerformance';
import type { UserPerformance } from '$lib/api/types';
import { userPerformanceText as t } from '$lib/text/user-performance';

/** The performance of one employee, exactly the content of the performance page of the employee app, including the range since joining. */
export class UserPerformanceDetailState {
	data = $state<UserPerformance | null>(null);
	loading = $state(true);
	error = $state('');
	range = $state<PerformanceRange>('cycle');

	private token = 0;

	constructor(readonly userId: string) {}

	/** A quiet reload (live signal) does not dim the page; its failure is still shown. */
	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		try {
			const data = await api.userPerformance.get(this.userId, this.range);
			if (token !== this.token) return;
			this.data = data;
			this.error = '';
		} catch (problem) {
			if (token === this.token) this.error = userMessage(problem, t.loadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
