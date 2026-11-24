<script lang="ts">
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import type { IngredientsState } from '../ingredients.svelte';
	import { ingredientText } from '$lib/text/ingredients';
	import { format } from '$lib/text/format';

	let { ingredients }: { ingredients: IngredientsState } = $props();
</script>

<Modal open title={ingredientText.catalogTitle} description={ingredientText.catalogDescription} size="md" busy={ingredients.busy} onclose={() => ingredients.closeDialogs()}>
	{#if ingredients.catalog.length === 0}
		<Notice text={ingredientText.catalogEmpty} />
	{:else}
		<ul class="flex max-h-96 flex-col divide-y divide-slate-100 overflow-y-auto">
			{#each ingredients.catalog as entry (entry.id)}
				<li class="flex items-center justify-between gap-3 py-2">
					<span class="min-w-0">
						<span class="block truncate text-sm text-slate-800">{entry.name}{entry.unit ? ` (${entry.unit})` : ''}</span>
						<span class="block text-xs text-slate-500">{entry.branch_count === 0 ? ingredientText.notUsed : format(ingredientText.usedByBranches, { count: entry.branch_count })}</span>
					</span>
					{#if entry.branch_count === 0}
						<DeleteButton small disabled={ingredients.busy} onclick={() => void ingredients.removeCatalogEntry(entry)} />
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
	{#if ingredients.actionError}<p class="mt-3 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{ingredients.actionError}</p>{/if}
	{#snippet footer()}
		<Button label={ingredientText.done} variant="primary" onclick={() => ingredients.closeDialogs()} />
	{/snippet}
</Modal>
