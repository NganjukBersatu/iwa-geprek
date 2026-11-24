<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { rupiahDigits } from '$lib/format/currency';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { parseNumber } from '$lib/format/number';
	import { untrack } from 'svelte';
	import type { MovementMode, StockRow } from '../stock-items.svelte';
	import { termText } from '$lib/text/terms';
	import { stockItemText } from '$lib/text/stock-items';
	import { format } from '$lib/text/format';

	let {
		item,
		mode,
		busy,
		error,
		onsave,
		onclose
	}: {
		item: StockRow;
		mode: MovementMode;
		busy: boolean;
		error: string;
		onsave: (body: { qty: string; unit_price?: string | null; note: string | null }) => void;
		onclose: () => void;
	} = $props();

	const MIN_REASON = 3;
	const receive = untrack(() => mode === 'receive');

	let qty = $state('');
	let price = $state('');
	let note = $state('');
	let problem = $state('');

	function submit(): void {
		const amount = parseNumber(qty);
		if (amount === null || amount === 0 || (receive && amount < 0)) return void (problem = receive ? stockItemText.quantityPositive : stockItemText.quantityNotZero);
		if (!receive && note.trim().length < MIN_REASON) return void (problem = stockItemText.reasonRequired);
		problem = '';
		if (receive) return onsave({ qty: String(amount), unit_price: price ? rupiahDigits(price) : null, note: note.trim() || null });
		onsave({ qty: String(amount), note: note.trim() });
	}
</script>

<Modal open title={receive ? format(stockItemText.receiveTitle, { name: item.menu_item_name }) : format(stockItemText.adjustTitle, { name: item.menu_item_name })} size="sm" {busy} {onclose}>
	<div class="flex flex-col gap-3">
		<TextField label={item.unit ? format(controlText.quantityWithUnitBrackets, { unit: item.unit }) : termText.quantity} inputmode="decimal" bind:value={qty} required hint={receive ? undefined : stockItemText.adjustQuantityHint} />
		{#if receive}
			<MoneyField label={stockItemText.unitCostRupiah} bind:value={price} hint={stockItemText.unitCostHint} />
		{/if}
		<TextField label={receive ? termText.note : stockItemText.reason} bind:value={note} maxlength={255} required={!receive} />
	</div>
	{#if problem || error}
		<p class="mt-4 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{problem || error}</p>
	{/if}
	{#snippet footer()}
		<CancelButton disabled={busy} onclick={onclose} />
		<SaveButton busy={busy} onclick={submit} />
	{/snippet}
</Modal>
