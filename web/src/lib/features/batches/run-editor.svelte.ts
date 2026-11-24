import { api } from '$lib/api';
import type { RunAnswerInput } from '$lib/api/batches';
import { userMessage } from '$lib/api/user-message';
import type { StoredRun } from '$lib/api/types';
import { batchRunText } from '$lib/text/batch-runs';

/** The changes an admin makes to one filling already sent: correcting its content, cancelling it, or deleting it. */
export class RunEditor {
	busy = $state(false);
	error = $state('');
	/** The template and saved answers while the correction form is open. */
	stored = $state<StoredRun | null>(null);
	confirming = $state<'cancel' | 'delete' | null>(null);

	/** [onchanged] runs after a change is saved, so the filling is read again. */
	constructor(private readonly onchanged: (action: 'fix' | 'cancel' | 'delete') => void) {}

	private async attempt(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		this.busy = true;
		this.error = '';
		try {
			await work();
			return true;
		} catch (problem) {
			this.error = userMessage(problem, fallback);
			return false;
		} finally {
			this.busy = false;
		}
	}

	async openFix(runId: string): Promise<void> {
		let found: StoredRun | null = null;
		const done = await this.attempt(async () => {
			found = await api.batches.storedRun(runId);
		}, batchRunText.loadFixFailed);
		if (done) this.stored = found;
	}

	async saveFix(runId: string, answers: RunAnswerInput[]): Promise<void> {
		if (!(await this.attempt(() => api.batches.fixRun(runId, answers), batchRunText.fixFailed))) return;
		this.stored = null;
		this.onchanged('fix');
	}

	ask(action: 'cancel' | 'delete'): void {
		this.error = '';
		this.confirming = action;
	}

	async confirm(runId: string): Promise<void> {
		const action = this.confirming;
		if (!action) return;
		const work = action === 'cancel' ? () => api.batches.cancelRun(runId) : () => api.batches.deleteRun(runId);
		if (!(await this.attempt(work, action === 'cancel' ? batchRunText.cancelFailed : batchRunText.deleteFailed))) return;
		this.confirming = null;
		this.onchanged(action);
	}

	close(): void {
		this.stored = null;
		this.confirming = null;
		this.error = '';
	}
}
