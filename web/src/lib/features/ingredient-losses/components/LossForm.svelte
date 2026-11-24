<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { api } from '$lib/api';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { formatNumber } from '$lib/format/currency';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { IngredientMovement, IngredientMovementUpdate, IngredientTrial, IngredientWaste, WasteCause } from '$lib/api/types';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { lossPath, PAGES } from '$lib/nav/pages';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { parseNumber } from '$lib/format/number';
	import { untrack } from 'svelte';
	import IngredientPicker from '../../ingredients/components/IngredientPicker.svelte';
	import { WASTE } from '../kinds';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { ingredientLossText } from '$lib/text/ingredient-losses';
	import { format } from '$lib/text/format';

	let {
		movement,
		kind,
		causes,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		movement: IngredientMovement | null;
		kind: string;
		causes: WasteCause[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: IngredientWaste | IngredientTrial | IngredientMovementUpdate, proof: File | null, outletId: string) => void;
		onclose: () => void;
	} = $props();

	const OTHER = 'lainnya';
	const current = untrack(() => movement);
	const isWaste = untrack(() => (current ? current.kind === WASTE : kind === WASTE));
	const createTitle = isWaste ? ingredientLossText.recordDamaged : ingredientLossText.recordRnd;
	const trail = [
		{ label: PAGES.ingredientWaste.label, href: PAGES.ingredientWaste.path },
		...(current ? [{ label: current.ingredient_name, href: lossPath(current.id) }, { label: actionText.edit }] : [{ label: createTitle }])
	];

	let ingredient = $state('');
	let qty = $state(current ? String(Math.abs(Number(current.qty))) : '');
	let cause = $state('');
	let note = $state(current?.note ?? '');
	let proof = $state<File | null>(null);
	let outletId = $state('');
	const causeChoices = $derived(causes.map((item) => ({ value: item.code, label: item.human_error ? format(ingredientLossText.negligenceLabel, { name: item.label }) : item.label })));
	const errors = new FieldErrors({ outlet_id: termText.branch, qty: termText.quantity, cause: ingredientLossText.cause, ingredient_id: termText.ingredient, note: isWaste ? termText.note : ingredientLossText.triedMenu }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	/** Sisa saldo yang akan tertinggal, ditanyakan sebelum disimpan supaya salah jumlah bisa dibetulkan. */
	type Shortfall = { name: string; unit: string; balance: number; qty: number; result: number };
	let shortfall = $state<Shortfall | null>(null);
	let checking = $state(false);
	let checkError = $state('');

	function send(amount: number): void {
		if (current) {
			onsave({ qty: String(amount), note: note.trim() || null }, proof, current.outlet_id);
			return;
		}
		if (isWaste) {
			onsave({ ingredient_id: ingredient, qty: String(amount), cause, note: note.trim() || null }, proof, outletId);
			return;
		}
		onsave({ ingredient_id: ingredient, qty: String(amount), note: note.trim() }, proof, outletId);
	}

	async function leavesNegative(amount: number): Promise<Shortfall | null> {
		const found = await api.ingredients.detail(ingredient);
		const balance = Number(found.balance);
		return balance - amount < 0 ? { name: found.name, unit: found.unit, balance, qty: amount, result: balance - amount } : null;
	}

	async function submit(): Promise<void> {
		if (checking) {
			return;
		}
		checkError = '';
		const found: Record<string, string> = {};
		const amount = parseNumber(qty);
		if (!current && !outletId) found.outlet_id = ingredientLossText.branchRequired;
		if (amount === null || amount <= 0) found.qty = ingredientLossText.quantityInvalid;
		if (!current && isWaste && !cause) found.cause = ingredientLossText.causeRequired;
		if (!current && outletId && !ingredient) found.ingredient_id = ingredientLossText.ingredientRequired;
		if (isWaste && cause === OTHER && !note.trim()) found.note = ingredientLossText.otherNeedsNote;
		if (!isWaste && !note.trim()) found.note = ingredientLossText.triedMenuRequired;
		if (!errors.check(found) || amount === null) {
			return;
		}
		if (current) {
			send(amount);
			return;
		}
		checking = true;
		let result: Shortfall | null;
		try {
			result = await leavesNegative(amount);
		} catch (failure) {
			checkError = userMessage(failure, ingredientLossText.balanceCheckFailed);
			return;
		} finally {
			checking = false;
		}
		if (result) {
			shortfall = result;
			return;
		}
		send(amount);
	}

	function confirmNegative(): void {
		const pending = shortfall;
		shortfall = null;
		if (pending) {
			send(pending.qty);
		}
	}
</script>

<FormPage
	title={current ? format(controlText.editName, { name: current.ingredient_name }) : createTitle}
	description={isWaste ? ingredientLossText.damagedFormDescription : ingredientLossText.rndFormDescription}
	stacked
	{trail}
	{busy}
	{onclose}
>
	<FormSection icon={isWaste ? 'trash' : 'flask'} title={isWaste ? ingredientLossText.damagedIngredients : ingredientLossText.rndIngredients} description={ingredientLossText.balanceNote}>
		<div class="grid gap-2 {current ? 'tablet:grid-cols-2' : isWaste ? 'tablet:grid-cols-3' : 'tablet:grid-cols-2'}">
			{#if !current}
				<BranchField bind:value={outletId} error={errors.get('outlet_id')} />
			{/if}
			<TextField label={current?.unit ? format(controlText.quantityWithUnitBrackets, { unit: current.unit }) : termText.quantity} inputmode="decimal" bind:value={qty} required hint={ingredientLossText.quantityHint} error={errors.get('qty')} />
			{#if isWaste && !current}
				<SelectField label={ingredientLossText.cause} bind:value={cause} options={causeChoices} empty={ingredientLossText.chooseCause} required error={errors.get('cause')} />
			{/if}
		</div>
		{#if !current && outletId}
			<div class="grid gap-2 tablet:grid-cols-2">
				<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('ingredient_id') ? true : undefined}>
					<IngredientPicker bind:value={ingredient} {outletId} />
					{#if errors.get('ingredient_id')}<p class="text-xs text-danger-700" role="alert">{errors.get('ingredient_id')}</p>{/if}
				</div>
			</div>
		{/if}
		<TextArea label={isWaste ? termText.note : ingredientLossText.triedMenu} bind:value={note} rows={2} maxlength={255} error={errors.get('note')} />
	</FormSection>
	<FormSection icon="photo" title={ingredientLossText.proofPhoto} description={ingredientLossText.proofHint}>
		<PhotoField label={ingredientLossText.proofPhoto} variant="chooser" current={current?.proof_url ?? null} alt={format(ingredientLossText.proofOf, { name: current?.ingredient_name ?? '' })} bind:file={proof} disabled={busy} />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}
	{#if checkError}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{checkError}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy || checking} onclick={() => void submit()} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>

<ConfirmDialog
	open={shortfall !== null}
	title={ingredientLossText.negativeTitle}
	confirmLabel={ingredientLossText.negativeConfirm}
	{busy}
	onconfirm={confirmNegative}
	oncancel={() => (shortfall = null)}
>
	{#if shortfall}
		{format(ingredientLossText.negativeNote, {
			name: shortfall.name,
			unit: shortfall.unit,
			balance: formatNumber(shortfall.balance),
			qty: formatNumber(shortfall.qty),
			result: formatNumber(shortfall.result)
		})}
	{/if}
</ConfirmDialog>
