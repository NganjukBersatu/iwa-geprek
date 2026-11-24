import { api } from '$lib/api';
import { ApiError } from '$lib/api/http';
import { userMessage } from '$lib/api/user-message';
import type { Branch, BranchRemoval, BranchUpdate } from '$lib/api/types';
import { forgetBranch } from '$lib/stores/branch';
import { toast } from '$lib/components/feedback/toast.svelte';
import { branchDetailText } from '$lib/text/branch-detail';
import { format } from '$lib/text/format';

// Satu langkah server sekitar 2 detik, jadi batas ini cukup untuk cabang bertahun-tahun tanpa berputar selamanya.
const MAX_REMOVAL_STEPS = 3000;

/** One branch: its data, the edit and close-or-reopen actions, and its permanent removal once it is closed. */
export class BranchDetailState {
	branch = $state<Branch | null>(null);
	loading = $state(true);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	/** What the server refused, by field name, for the edit form to show under each field. */
	fieldErrors = $state<Record<string, string>>({});
	toggling = $state(false);
	removing = $state(false);
	removal = $state<BranchRemoval | null>(null);
	removed = $state(false);
	private token = 0;

	constructor(readonly id: string) {}

	/** Reloads without dimming the screen: what is shown stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		try {
			const branch = await api.branches.detail(this.id);
			if (token !== this.token) return;
			this.branch = branch;
			this.error = '';
		} catch (error) {
			if (token !== this.token) return;
			if (!quiet) {
				this.branch = null;
				this.error = userMessage(error, branchDetailText.loadFailed);
			}
		} finally {
			if (token === this.token) this.loading = false;
		}
	}

	askToggle(): void {
		this.actionError = '';
		this.toggling = true;
	}

	askRemove(): void {
		this.actionError = '';
		this.removing = true;
	}

	closeDialogs(): void {
		if (this.busy) return;
		this.toggling = false;
		this.removing = false;
		this.actionError = '';
		this.fieldErrors = {};
	}

	/** Langkah hapus dipanggil berulang sampai server menyatakan selesai; bila terputus, menekan lagi melanjutkan sisanya. */
	async confirmRemove(): Promise<void> {
		const current = this.branch;
		if (!current || this.busy) return;
		this.busy = true;
		this.actionError = '';
		try {
			for (let round = 0; round < MAX_REMOVAL_STEPS; round++) {
				const step = await api.branches.removeStep(this.id, current.name);
				this.removal = step;
				if (step.done) {
					forgetBranch(this.id);
					this.removed = true;
					return;
				}
			}
			this.actionError = branchDetailText.removeUnfinished;
		} catch (error) {
			this.actionError = userMessage(error, branchDetailText.removeStopped);
			void this.load(true);
		} finally {
			this.busy = false;
		}
	}

	/** True when the branch was saved, so the edit page returns to it. */
	async save(body: BranchUpdate): Promise<boolean> {
		const current = this.branch;
		if (!current) return false;
		if (!(await this.attempt(async () => (this.branch = await api.branches.update(current.id, body)), branchDetailText.saveFailed))) return false;
		toast.show(format(branchDetailText.saved, { name: this.branch?.name ?? current.name }));
		return true;
	}

	async confirmToggle(): Promise<void> {
		const current = this.branch;
		if (!current) return;
		const done = await this.attempt(async () => (this.branch = await api.branches.update(current.id, { is_active: !current.is_active })), branchDetailText.toggleFailed);
		if (!done) return;
		this.toggling = false;
		toast.show(format(current.is_active ? branchDetailText.closedDone : branchDetailText.reopenedDone, { name: current.name }));
		await this.load(true);
	}

	private async attempt(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		this.busy = true;
		this.actionError = '';
		this.fieldErrors = {};
		try {
			await work();
			return true;
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			this.actionError = userMessage(error, fallback);
			return false;
		} finally {
			this.busy = false;
		}
	}
}
