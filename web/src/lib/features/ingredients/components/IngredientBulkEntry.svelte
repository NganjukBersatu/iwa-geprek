<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { IngredientCreate, IngredientOptions } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { ingredientText } from '$lib/text/ingredients';

	let options = $state<IngredientOptions | null>(null);
	let error = $state('');

	async function load(): Promise<void> {
		error = '';
		try {
			options = await api.ingredients.options();
		} catch (cause) {
			error = userMessage(cause, ingredientText.unitsLoadFailed);
		}
	}

	onMount(() => void load());

	const entryColumns = $derived<Field[]>(
		options
			? [
					{ key: 'name', label: termText.name, required: true },
					{ key: 'unit_id', label: termText.unit, kind: 'select', required: true, options: options.units.map((item) => ({ value: item.id, label: item.name })) },
					{ key: 'category_id', label: termText.category, kind: 'select', options: options.categories.map((item) => ({ value: item.id, label: item.name })) },
					{ key: 'package_price', label: ingredientText.packagePrice, kind: 'number' },
					{ key: 'package_size', label: ingredientText.packageSize, kind: 'number' },
					{ key: 'minimum', label: ingredientText.minimum, kind: 'number' }
				]
			: []
	);
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle" title={actionText.pageLoadFailed}>
		{error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void load()} />
		{/snippet}
	</Banner>
{:else if options}
	<BulkEntryDialog
		asPage
		title={ingredientText.bulkTitle}
		hint={ingredientText.bulkHint}
		columns={entryColumns}
		withBranch
		submit={(rows, outletId) => api.ingredients.bulk.createIn(outletId, rows as unknown as IngredientCreate[])}
		submitLabel="Simpan semua bahan"
		onclose={() => void goto(PAGES.ingredients.path)}
	/>
{:else}
	<Notice loading text={ingredientText.unitsLoading} />
{/if}
