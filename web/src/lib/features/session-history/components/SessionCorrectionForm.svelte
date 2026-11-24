<script lang="ts">
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { rupiahValue } from '$lib/format/currency';
	import type { SessionCorrection, SessionHistoryRow } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { PAGES, sessionPath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { sessionHistoryText } from '$lib/text/session-history';
	import { format } from '$lib/text/format';

	let {
		row,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		row: SessionHistoryRow;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: SessionCorrection) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => row);
	const actualEditable = !current.running && !current.three_parts;
	const trail = [
		{ label: PAGES.sessionHistory.label, href: PAGES.sessionHistory.path },
		{ label: format(sessionHistoryText.sessionTitle, { name: current.cashier_username }), href: sessionPath(current.id) },
		{ label: sessionHistoryText.correction }
	];

	let opening = $state(String(Math.round(Number(current.opening_cash))));
	let actual = $state(current.actual_cash === null ? '' : String(Math.round(Number(current.actual_cash))));
	let note = $state(current.note ?? '');
	const errors = new FieldErrors({ opening_cash: sessionHistoryText.openingFloat, actual_cash: sessionHistoryText.actualMoney, note: termText.note }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		if (opening.trim() === '') found.opening_cash = sessionHistoryText.openingFloatRequired;
		if (!errors.check(found)) return;
		const body: SessionCorrection = { opening_cash: String(rupiahValue(opening)), note: note.trim() };
		if (actualEditable && actual.trim() !== '') body.actual_cash = String(rupiahValue(actual));
		onsave(body);
	}
</script>

<FormPage title={format(sessionHistoryText.correctSessionNamed, { name: current.cashier_username })} description={sessionHistoryText.correctionRecalculates} stacked {trail} {busy} {onclose}>
	<FormSection icon="cash" title={sessionHistoryText.sessionMoney} description={sessionHistoryText.correctionReplaces}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<MoneyField label={sessionHistoryText.openingFloatRupiah} bind:value={opening} required error={errors.get('opening_cash')} />
			{#if actualEditable}
				<MoneyField label={sessionHistoryText.actualMoneyRupiah} bind:value={actual} hint={sessionHistoryText.actualMoneyHint} error={errors.get('actual_cash')} />
			{/if}
		</div>
		{#if !actualEditable && current.three_parts && !current.running}
			<p class="text-xs text-slate-500">{sessionHistoryText.threePartsNote}</p>
		{/if}
	</FormSection>
	<FormSection icon="notes" title={termText.note} description={sessionHistoryText.correctionReason}>
		<TextArea label={termText.note} bind:value={note} rows={3} maxlength={500} error={errors.get('note')} />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
