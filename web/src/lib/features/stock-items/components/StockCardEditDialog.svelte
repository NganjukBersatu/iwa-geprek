<script lang="ts">
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { rupiahDigits } from '$lib/format/currency';
	import type { StockCard, StockCardUpdate } from '$lib/api/types';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { parseNumber } from '$lib/format/number';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { stockItemText } from '$lib/text/stock-items';
	import { format } from '$lib/text/format';

	let {
		card,
		busy,
		error,
		onsave,
		onremove,
		onclose
	}: {
		card: StockCard;
		busy: boolean;
		error: string;
		onsave: (body: StockCardUpdate) => void;
		onremove: () => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => card);

	let qty = $state(String(Number(current.qty)));
	let price = $state(current.unit_price === null ? '' : String(Math.round(Number(current.unit_price))));
	let note = $state(current.note ?? '');
	let problem = $state('');

	function submit(): void {
		const amount = parseNumber(qty);
		if (amount === null || amount === 0) return void (problem = stockItemText.quantityNotZero);
		problem = '';
		onsave({ qty: String(amount), unit_price: price ? rupiahDigits(price) : undefined, note: note.trim() || null });
	}
</script>

<Modal open title={format(stockItemText.editCardTitle, { name: current.menu_item_name })} description={stockItemText.cardKindUnchanged} size="sm" {busy} {onclose}>
	<div class="flex flex-col gap-3">
		<TextField label={termText.quantity} inputmode="decimal" bind:value={qty} required />
		{#if current.kind === 'masuk'}
			<MoneyField label={stockItemText.unitCostRupiah} bind:value={price} />
		{/if}
		<TextField label={termText.note} bind:value={note} maxlength={255} />
	</div>
	{#if problem || error}
		<p class="mt-4 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{problem || error}</p>
	{/if}
	{#snippet footer()}
		<span class="tablet:mr-auto"><DeleteButton disabled={busy} onclick={onremove} /></span>
		<CancelButton disabled={busy} onclick={onclose} />
		<SaveButton busy={busy} onclick={submit} />
	{/snippet}
</Modal>
