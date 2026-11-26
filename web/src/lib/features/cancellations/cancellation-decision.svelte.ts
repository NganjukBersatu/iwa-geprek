import { api } from '$lib/api';
import type { Cancellation } from '$lib/api/types';
import { userMessage } from '$lib/api/user-message';
import { toast } from '$lib/components/feedback/toast.svelte';
import { cancellationText } from '$lib/text/cancellations';
import { DayWarning } from '../deposits/day-warning.svelte';

/** Sama dengan MAX_NOTE_LENGTH di app.core.orders.cancellations. */
export const DECISION_NOTE_MAX = 500;

export type DecisionKind = 'approve' | 'reject';

/** The decision on one request: both answers wait for a confirmation with an optional note, since neither can be taken back; approving also warns about deposited days. */
export class CancellationDecisionState {
	busy = $state(false);
	error = $state('');
	confirming = $state<DecisionKind | null>(null);
	note = $state('');
	readonly warning = new DayWarning();

	constructor(private readonly reload: () => Promise<void>) {}

	ask(request: Cancellation, kind: DecisionKind): void {
		this.error = '';
		this.note = '';
		this.confirming = kind;
		if (kind === 'approve') void this.warning.read([{ outlet_id: request.outlet_id, day: request.order_business_day }]);
	}

	close(): void {
		this.confirming = null;
		this.error = '';
		this.note = '';
		this.warning.clear();
	}

	async confirm(request: Cancellation): Promise<void> {
		const kind = this.confirming;
		if (kind === null) return;
		const approve = kind === 'approve';
		this.busy = true;
		this.error = '';
		try {
			await api.cancellations.decide(request.id, { approve, note: this.note.trim() || null });
		} catch (failure) {
			this.error = userMessage(failure, cancellationText.decisionFailed);
			return;
		} finally {
			this.busy = false;
		}
		this.close();
		toast.show(approve ? cancellationText.approved : cancellationText.rejected);
		await this.reload();
	}
}
