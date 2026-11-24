<script lang="ts">
	import type { CatalogEntry, Ingredient } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import { ingredientText } from '$lib/text/ingredients';
	import { format } from '$lib/text/format';

	let {
		ingredient,
		catalog,
		busy,
		error,
		onconfirm,
		onclose
	}: {
		ingredient: Ingredient;
		catalog: CatalogEntry[];
		busy: boolean;
		error: string;
		/** The chosen catalog entry, or null to make a new entry from this ingredient. */
		onconfirm: (catalogId: string | null) => void;
		onclose: () => void;
	} = $props();

	const NEW_ENTRY = '__new__';

	let choice = $state(NEW_ENTRY);

	const choices = $derived([
		{ value: NEW_ENTRY, label: ingredientText.createCatalogEntry },
		...catalog.filter((entry) => entry.unit === ingredient.unit).map((entry) => ({ value: entry.id, label: format(ingredientText.catalogEntryUsage, { name: entry.name, count: entry.branch_count }) }))
	]);
</script>

<Modal open title={format(ingredientText.linkToCatalogTitle, { name: ingredient.name })} description={ingredientText.linkDescription} size="sm" {busy} {onclose}>
	<SelectField label={ingredientText.catalogEntry} bind:value={choice} options={choices} />
	{#if error}<p class="mt-3 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{error}</p>{/if}
	{#snippet footer()}
		<CancelButton disabled={busy} onclick={onclose} />
		<Button label={busy ? ingredientText.linking : ingredientText.link} variant="primary" disabled={busy} onclick={() => onconfirm(choice === NEW_ENTRY ? null : choice)} />
	{/snippet}
</Modal>
