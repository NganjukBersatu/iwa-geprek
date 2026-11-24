<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import IngredientCountsView from '$lib/features/ingredient-counts/components/CountsView.svelte';
	import { IngredientCountsState } from '$lib/features/ingredient-counts/ingredient-counts.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { pageText } from '$lib/text/pages';

	const counts = new IngredientCountsState();
</script>

<ManageShell
	manage={counts}
	filters={counts.filters}
	title={pageText.stockCountTitle}
	description={pageText.stockCountDescription}
	loadingText={pageText.loadingCounts}
>
	{#snippet actions()}
		<Button label={pageText.openingStock} icon="table-plus" compact onclick={() => counts.openOpening()} />
	{/snippet}
	{#snippet children()}
		<IngredientCountsView {counts} />
	{/snippet}
</ManageShell>
