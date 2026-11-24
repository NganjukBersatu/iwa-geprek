<script lang="ts">
	import { collectPages } from '../../manage/collect';
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import type { Ingredient, IngredientReceipt } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import { termText } from '$lib/text/terms';
	import { ingredientReceiptText } from '$lib/text/ingredient-receipts';


	let ingredients = $state<Ingredient[]>([]);
	let error = $state('');

	/** The ingredients of the branch chosen on the page. */
	async function loadIngredients(outletId: string): Promise<void> {
		ingredients = [];
		error = '';
		if (!outletId) return;
		try {
			ingredients = await collectPages((page, size) => api.ingredients.list({ page, size, outlet_id: outletId }));
		} catch (cause) {
			error = userMessage(cause, controlText.ingredientsLoadFailed);
		}
	}

	const entryColumns = $derived<Field[]>([
		{ key: 'ingredient_id', label: termText.ingredient, kind: 'select', required: true, options: ingredients.map((item) => ({ value: item.id, label: `${item.name} (${item.unit})` })) },
		{ key: 'qty', label: termText.quantity, kind: 'number', required: true },
		{ key: 'note', label: termText.note }
	]);
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle">{error}</Banner>
{/if}
<BulkEntryDialog
	asPage
	title={ingredientReceiptText.bulkTitle}
	hint={ingredientReceiptText.bulkHint}
	columns={entryColumns}
	withBranch
	onbranch={(outletId) => void loadIngredients(outletId)}
	submit={(rows, outletId) => api.ingredientMovements.bulk.createIn(outletId, rows as unknown as IngredientReceipt[])}
	submitLabel="Simpan semua"
	onclose={() => void goto(PAGES.ingredientReceipts.path)}
/>
