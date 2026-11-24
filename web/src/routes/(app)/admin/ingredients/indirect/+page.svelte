<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import Button from '$lib/components/button/Button.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { ingredientColumns } from '$lib/features/ingredients/columns';
	import IngredientsView from '$lib/features/ingredients/components/IngredientsView.svelte';
	import { IngredientsState } from '$lib/features/ingredients/ingredients.svelte';
	import { lossColumns } from '$lib/features/ingredient-losses/columns';
	import LossesView from '$lib/features/ingredient-losses/components/LossesView.svelte';
	import { IngredientLossesState } from '$lib/features/ingredient-losses/ingredient-losses.svelte';
	import { USE } from '$lib/features/ingredient-losses/kinds';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { ingredientNewPath, USAGE_TAB, usageNewPath } from '$lib/nav/pages';
	import { controlText } from '$lib/text/controls';
	import { pageText } from '$lib/text/pages';

	const LIST_TAB = 'list';

	const ingredients = new IngredientsState(true);
	const usage = new IngredientLossesState(true);

	let tab = $state(page.url.searchParams.get('tab') === USAGE_TAB ? USAGE_TAB : LIST_TAB);

	const tabs = [
		{ key: LIST_TAB, label: pageText.indirectListTab, icon: 'list-details' },
		{ key: USAGE_TAB, label: pageText.usageTab, icon: 'flame' }
	];
</script>

{#snippet bar()}
	<Tabs {tabs} label={pageText.pageContents} bind:value={tab} class="mb-4" />
{/snippet}

{#key tab}
	{#if tab === USAGE_TAB}
		<ManageShell manage={usage} filters={usage.filters} title={pageText.indirectTitle} description={pageText.indirectDescription} loadingText={pageText.loadingUsage}>
			{#snippet actions()}
				<Button label={pageText.recordUsage} icon="plus" variant="primary" compact onclick={() => void goto(usageNewPath())} />
				<MoreButton exporter={{ title: pageText.exportTitles.usage, columns: lossColumns(USE), rows: () => usage.exportRows() }} />
			{/snippet}
			{#snippet children()}
				{@render bar()}
				<LossesView losses={usage} />
			{/snippet}
		</ManageShell>
	{:else}
		<ManageShell manage={ingredients} filters={ingredients.filters} title={pageText.indirectTitle} description={pageText.indirectDescription} loadingText={pageText.loadingIndirect}>
			{#snippet actions()}
				<Button label={pageText.catalog} icon="books" compact onclick={() => void ingredients.openCatalog()} />
				<Button label={controlText.addIngredient} icon="plus" variant="primary" compact onclick={() => void goto(ingredientNewPath(true))} />
				<MoreButton selection={ingredients.selection} exporter={{ title: pageText.exportTitles.indirect, columns: ingredientColumns, rows: () => ingredients.exportRows() }} />
			{/snippet}
			{#snippet children()}
				{@render bar()}
				<IngredientsView {ingredients} />
			{/snippet}
		</ManageShell>
	{/if}
{/key}
