<script lang="ts">
	import { goto } from '$app/navigation';
	import { userMessage } from '$lib/api/user-message';
	import { api } from '$lib/api';
	import type { SessionHistoryRow, SessionImpact, SessionIntervention } from '$lib/api/types';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { formatNumber } from '$lib/format/currency';
	import { editAddress } from '../../record-detail/edit-address.svelte';
	import SessionCloseDialog from '../../session-history/components/SessionCloseDialog.svelte';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import { DayWarning } from '../../deposits/day-warning.svelte';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	let { row, onchanged, ondeleted }: { row: SessionHistoryRow; onchanged: () => void; ondeleted: () => void } = $props();

	let closingSession = $state(false);
	let deleting = $state<SessionImpact | null>(null);
	let busy = $state(false);
	let error = $state('');
	const warning = new DayWarning();

	async function run(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		busy = true;
		error = '';
		try {
			await work();
			return true;
		} catch (problem) {
			error = userMessage(problem, fallback);
			return false;
		} finally {
			busy = false;
		}
	}

	function close(): void {
		closingSession = false;
		deleting = null;
		error = '';
		warning.clear();
	}

	async function closeSession(body: SessionIntervention): Promise<void> {
		if (!(await run(() => api.sessions.close(row.id, body), sessionDetailText.sessionCloseFailed))) return;
		close();
		onchanged();
	}

	async function askDelete(): Promise<void> {
		void warning.read([{ outlet_id: row.outlet_id, day: row.business_day }]);
		await run(async () => {
			deleting = await api.sessions.impact(row.id);
		}, sessionDetailText.sessionCheckFailed);
	}

	async function removeSession(): Promise<void> {
		if (!(await run(() => api.sessions.remove(row.id), sessionDetailText.sessionRemoveFailed))) return;
		close();
		ondeleted();
	}
</script>

{#if row.running}
	<Button label={sessionDetailText.closeSession} icon="lock" disabled={busy} onclick={() => (closingSession = true)} />
{/if}
<Button label={sessionDetailText.correctSession} icon="pencil" variant="tertiary" disabled={busy} onclick={() => void goto(editAddress().editPath)} />
<DeleteButton label={sessionDetailText.removeSession} disabled={busy} onclick={() => void askDelete()} />

{#if closingSession}
	<SessionCloseDialog {row} {busy} {error} onsave={(body) => void closeSession(body)} onclose={close} />
{/if}

<ConfirmDialog open={deleting !== null} title={format(sessionDetailText.removeSessionNamedTitle, { name: row.cashier_username })} confirmLabel="Hapus sesi" danger busy={busy || warning.checking} {error} onconfirm={() => void removeSession()} oncancel={close}>
	<RichText template={sessionDetailText.sessionOrdersRemovedNote} values={{ count: formatNumber(deleting?.orders ?? 0, 0) }} />
	<span class="mt-2 block"><RichText template={sessionDetailText.expensesKeptNote} values={{ count: formatNumber(deleting?.expenses ?? 0, 0) }} /></span>
	<DepositedDayWarning {warning} />
</ConfirmDialog>
