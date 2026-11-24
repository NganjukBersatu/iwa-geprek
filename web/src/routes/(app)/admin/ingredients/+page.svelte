<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import { ingredientBulkPath, ingredientNewPath } from '$lib/nav/pages';
	import Button from '$lib/components/button/Button.svelte';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import IngredientsView from '$lib/features/ingredients/components/IngredientsView.svelte';
	import { IngredientsState } from '$lib/features/ingredients/ingredients.svelte';
	import { ingredientColumns } from '$lib/features/ingredients/columns';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { pageText } from '$lib/text/pages';

	const ingredients = new IngredientsState();
</script>

<ManageShell
	manage={ingredients}
	filters={ingredients.filters}
	title={pageText.ingredientsTitle}
	description={pageText.ingredientsDescription}
	loadingText="Memuat bahan..."
>
	{#snippet actions()}
		<Button label={pageText.catalog} icon="books" compact onclick={() => void ingredients.openCatalog()} />
		<AddButton label={controlText.addIngredient} onone={() => void goto(ingredientNewPath())} onmany={() => void goto(ingredientBulkPath())} />
		<MoreButton selection={ingredients.selection} exporter={{ title: pageText.exportTitles.ingredients, columns: ingredientColumns, rows: () => ingredients.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<IngredientsView {ingredients} />
	{/snippet}
</ManageShell>
