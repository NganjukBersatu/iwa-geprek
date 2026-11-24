<script lang="ts">
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { untrack } from 'svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { todayIso } from '$lib/date/range';
	import { formatRupiah, rupiahDigits } from '$lib/format/currency';
	import type { DepositsState } from '../deposits.svelte';
	import { rangesOf } from '../format';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { DayWarning } from '../day-warning.svelte';
	import DepositedDayWarning from './DepositedDayWarning.svelte';
	import { termText } from '$lib/text/terms';
	import { depositText } from '$lib/text/deposits';
	import { format } from '$lib/text/format';

	let { deposits }: { deposits: DepositsState } = $props();

	const picked = untrack(() => deposits.form?.days ?? []);

	let outletId = $state('');
	let date = $state(todayIso());
	let amount = $state('');
	let note = $state('');
	let photo = $state<File | null>(null);
	const errors = new FieldErrors(
		{ outlet_id: termText.branch, deposit_date: depositText.depositDate, amount: depositText.amountHandedOver, note: termText.note },
		() => deposits.fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(deposits.fieldErrors).length > 0) void focusRefused();
	});

	// Only the days that still hold money at the chosen branch can be settled.
	const days = $derived(picked.filter((day) => deposits.formLeft([day]) > 0));
	const left = $derived(deposits.formLeft(days));

	// A day whose session still runs can still change after it is handed over.
	const warning = new DayWarning();
	whenChanged(
		() => (outletId ? days.map((day) => ({ outlet_id: outletId, day })) : []),
		(keys) => void warning.read(keys)
	);

	function changeBranch(id: string): void {
		amount = '';
		void deposits.loadFormDays(id).then(() => (amount = String(Math.round(deposits.formLeft(picked.filter((day) => deposits.formLeft([day]) > 0))))));
	}

	function submit(): void {
		const digits = rupiahDigits(amount);
		const found: Record<string, string> = {};
		if (!outletId) found.outlet_id = depositText.branchRequired;
		else if (days.length === 0) found.outlet_id = depositText.noHeldDays;
		if (!date) found.deposit_date = depositText.dateRequired;
		if (!digits || Number(digits) <= 0) found.amount = depositText.amountRequired;
		if (!errors.check(found)) return;
		void deposits.save({ deposit_date: date, amount: digits, note: note.trim() || null, days }, photo, outletId);
	}
</script>

<Modal open title={depositText.recordDeposit} description={format(depositText.depositFormSummary, { count: days.length, dates: rangesOf(days), remaining: formatRupiah(left) })} size="sm" busy={deposits.busy} onclose={() => deposits.closeDialogs()}>
	<div class="flex flex-col gap-4">
		<BranchField bind:value={outletId} onchange={changeBranch} error={errors.get('outlet_id')} />
		<TextField label={depositText.depositDate} type="date" bind:value={date} max={todayIso()} required error={errors.get('deposit_date')} />
		<MoneyField label={depositText.amountHandedOverRupiah} bind:value={amount} required error={errors.get('amount')} />
		<TextField label={termText.note} bind:value={note} maxlength={255} error={errors.get('note')} />
		<PhotoField label={depositText.receiptPhoto} current={null} alt={depositText.receiptPreview} bind:file={photo} disabled={deposits.busy} />
		<DepositedDayWarning {warning} mode="deposit" />
		{#if deposits.actionError && errors.count === 0}
			<p class="rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{deposits.actionError}</p>
		{/if}
	</div>

	{#snippet footer()}
		<CancelButton disabled={deposits.busy} onclick={() => deposits.closeDialogs()} />
		<SaveButton label={depositText.saveDeposit} busy={deposits.busy} disabled={warning.checking} onclick={submit} />
	{/snippet}
</Modal>
