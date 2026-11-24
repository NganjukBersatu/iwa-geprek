<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import Banner from '$lib/components/card/Banner.svelte';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { IngredientMovement, IngredientMovementUpdate, IngredientReceipt } from '$lib/api/types';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { PAGES, receiptPath } from '$lib/nav/pages';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { parseNumber } from '$lib/format/number';
	import { untrack } from 'svelte';
	import IngredientPicker from '../../ingredients/components/IngredientPicker.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { ingredientReceiptText } from '$lib/text/ingredient-receipts';
	import { format } from '$lib/text/format';

	let {
		movement,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		movement: IngredientMovement | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: IngredientReceipt | IngredientMovementUpdate, proof: File | null, outletId: string) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => movement);
	const trail = [
		{ label: PAGES.ingredientReceipts.label, href: PAGES.ingredientReceipts.path },
		...(current ? [{ label: current.ingredient_name, href: receiptPath(current.id) }, { label: actionText.edit }] : [{ label: ingredientReceiptText.recordReceipt }])
	];

	let ingredient = $state('');
	let qty = $state(current ? String(Math.abs(Number(current.qty))) : '');
	let note = $state(current?.note ?? '');
	let proof = $state<File | null>(null);
	let outletId = $state('');
	const errors = new FieldErrors({ outlet_id: termText.branch, ingredient_id: termText.ingredient, qty: termText.quantity, note: termText.note }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		const amount = parseNumber(qty);
		if (!current && !outletId) found.outlet_id = ingredientReceiptText.branchRequired;
		if (!current && outletId && !ingredient) found.ingredient_id = ingredientReceiptText.ingredientRequired;
		if (amount === null || amount <= 0) found.qty = ingredientReceiptText.quantityInvalid;
		if (!errors.check(found)) return;
		if (amount === null) return;
		if (current) return onsave({ qty: String(amount), note: note.trim() || null }, proof, current.outlet_id);
		onsave({ ingredient_id: ingredient, qty: String(amount), note: note.trim() || null }, proof, outletId);
	}
</script>

<FormPage
	title={current ? format(controlText.editName, { name: current.ingredient_name }) : ingredientReceiptText.recordReceipt}
	description={ingredientReceiptText.formDescription}
	stacked
	{trail}
	{busy}
	{onclose}
>
	<FormSection icon="package" title={ingredientReceiptText.receipt} description={ingredientReceiptText.ingredientSectionDescription}>
		{#if !current}
			<div class="grid gap-2 tablet:grid-cols-2">
				<BranchField bind:value={outletId} error={errors.get('outlet_id')} />
				{#if outletId}
					<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('ingredient_id') ? true : undefined}>
						<IngredientPicker bind:value={ingredient} {outletId} />
						{#if errors.get('ingredient_id')}<p class="text-xs text-danger-700" role="alert">{errors.get('ingredient_id')}</p>{/if}
					</div>
				{/if}
			</div>
		{/if}
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={current?.unit ? format(controlText.quantityWithUnitBrackets, { unit: current.unit }) : termText.quantity} inputmode="decimal" bind:value={qty} required error={errors.get('qty')} />
		</div>
		<TextArea label={termText.note} bind:value={note} rows={2} maxlength={255} error={errors.get('note')} />
	</FormSection>
	<FormSection icon="receipt" title={ingredientReceiptText.proofPhoto} description={ingredientReceiptText.proofDescription}>
		<PhotoField label={ingredientReceiptText.proofPhoto} variant="chooser" current={current?.proof_url ?? null} alt={format(ingredientReceiptText.proofOf, { name: current?.ingredient_name ?? '' })} bind:file={proof} disabled={busy} />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
