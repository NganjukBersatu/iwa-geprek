import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { BranchPeriod, BranchPeriodChange } from '$lib/api/types';
import { BRANCH_TABS, branchPath, branchPeriodPath } from '$lib/nav/pages';
import { branchPeriodText as text } from '$lib/text/branch-periods';

/** Satu periode cabang dibuka sebagai halaman sendiri; aksinya (ubah, kembalikan ke pola) ada di header halaman ini. */
export class BranchPeriodDetailState {
	data = $state<BranchPeriod | null>(null);
	loading = $state(true);
	error = $state('');
	editing = $state(false);
	resetting = $state(false);
	busy = $state(false);
	actionError = $state('');

	private token = 0;

	constructor(
		readonly outletId: string,
		readonly start: string
	) {}

	async load(): Promise<void> {
		const token = ++this.token;
		this.loading = true;
		try {
			const periods = await api.outlets.periods(this.outletId);
			if (token !== this.token) return;
			this.data = periods.find((period) => period.start === this.start) ?? null;
			this.error = this.data ? '' : text.gone;
		} catch (problem) {
			if (token === this.token) this.error = userMessage(problem, text.loadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}

	openEdit(): void {
		this.actionError = '';
		this.editing = true;
	}

	askReset(): void {
		this.actionError = '';
		this.resetting = true;
	}

	closeDialogs(): void {
		this.editing = false;
		this.resetting = false;
		this.actionError = '';
	}

	async save(change: BranchPeriodChange): Promise<void> {
		await this.run(async () => {
			await api.branches.adjustPeriod(this.outletId, this.start, change);
			// Periode dikenali dari tanggal mulainya, jadi tanggal mulai yang bergeser berarti alamat halaman ikut pindah.
			if (change.start === this.start) await this.load();
			else await goto(branchPeriodPath(this.outletId, change.start), { replaceState: true });
		}, text.saveFailed);
	}

	async reset(): Promise<void> {
		await this.run(async () => {
			await api.branches.resetPeriod(this.outletId, this.start);
			await goto(branchPath(this.outletId, BRANCH_TABS.periods));
		}, text.resetFailed);
	}

	private async run(work: () => Promise<void>, fallback: string): Promise<void> {
		this.busy = true;
		try {
			await work();
			this.closeDialogs();
		} catch (problem) {
			this.actionError = userMessage(problem, fallback);
		} finally {
			this.busy = false;
		}
	}
}
