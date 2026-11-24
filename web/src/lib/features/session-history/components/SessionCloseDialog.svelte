<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { userMessage } from '$lib/api/user-message';
	import { onMount, untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { SessionClosing, SessionHistoryRow, SessionIntervention } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { sessionHistoryText } from '$lib/text/session-history';
	import { format } from '$lib/text/format';

	let { row, busy, error, onsave, onclose }: { row: SessionHistoryRow; busy: boolean; error: string; onsave: (body: SessionIntervention) => void; onclose: () => void } = $props();

	const current = untrack(() => row);
	const MIN_REASON = 3;

	let closing = $state<SessionClosing | null>(null);
	let loadError = $state('');
	let cash = $state('');
	let float = $state('');
	let shopping = $state('');
	let revenue = $state('');
	let note = $state('');
	let problem = $state('');

	const expected = (amount: string | null | undefined) => (amount == null ? undefined : format(sessionHistoryText.expectedAmount, { amount: formatRupiah(amount) }));

	onMount(async () => {
		try {
			closing = await api.sessions.closing(current.id);
		} catch (failure) {
			loadError = userMessage(failure, sessionHistoryText.summaryLoadFailed);
		}
	});

	function submit(): void {
		if (!closing) {
			return;
		}
		if (note.trim().length < MIN_REASON) {
			problem = sessionHistoryText.reasonRequired;
			return;
		}
		const body: SessionIntervention = { note: note.trim() };
		if (closing.three_parts) {
			if (float === '' || shopping === '' || revenue === '') {
				problem = sessionHistoryText.threePartsRequired;
				return;
			}
			body.actual_float = float;
			body.actual_shopping = shopping;
			body.actual_revenue = revenue;
		} else {
			if (cash === '') {
				problem = sessionHistoryText.actualRequired;
				return;
			}
			body.actual_cash = cash;
		}
		problem = '';
		onsave(body);
	}
</script>

<Modal open title={format(sessionHistoryText.closeSessionNamed, { name: current.cashier_username })} description={sessionHistoryText.closeIntervention} size="sm" {busy} {onclose}>
	<div class="flex flex-col gap-4">
		<Banner tone="warning" icon="alert-triangle">
			{sessionHistoryText.closeHeldOrdersNote}
		</Banner>

		{#if loadError}
			<Banner tone="danger" icon="alert-triangle">{loadError}</Banner>
		{:else if !closing}
			<p class="text-sm text-slate-500">{sessionHistoryText.summaryLoading}</p>
		{:else if closing.three_parts}
			<MoneyField label={sessionHistoryText.floatRupiah} bind:value={float} hint={expected(closing.planned_float)} required />
			<MoneyField label={sessionHistoryText.spendingRupiah} bind:value={shopping} hint={expected(closing.planned_shopping)} required />
			<MoneyField label={sessionHistoryText.cashRevenueRupiah} bind:value={revenue} hint={expected(closing.expected_revenue)} required />
		{:else}
			<MoneyField label={sessionHistoryText.actualDrawerRupiah} bind:value={cash} hint={expected(closing.expected_cash)} required />
		{/if}

		<TextArea label={sessionHistoryText.closeReason} bind:value={note} rows={3} maxlength={500} />
	</div>

	{#if problem || error}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{problem || error}</Banner></div>
	{/if}

	{#snippet footer()}
		<CancelButton disabled={busy} onclick={onclose} />
		<Button label={busy ? controlText.closing : sessionHistoryText.closeSession} variant="danger" disabled={busy || !closing} onclick={submit} />
	{/snippet}
</Modal>
