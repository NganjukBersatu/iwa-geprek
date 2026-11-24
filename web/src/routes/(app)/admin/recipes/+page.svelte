<script lang="ts">
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import RecipesView from '$lib/features/recipes/components/RecipesView.svelte';
	import { RecipesState } from '$lib/features/recipes/recipes.svelte';
	import { pageText } from '$lib/text/pages';

	const recipes = new RecipesState();
</script>

<ManageShell manage={recipes} filters={recipes.filters} title={pageText.recipesTitle} description={pageText.recipesDescription} loadingText={pageText.loadingRecipes}>
	{#snippet children()}
		<RecipesView {recipes} />
	{/snippet}
</ManageShell>
