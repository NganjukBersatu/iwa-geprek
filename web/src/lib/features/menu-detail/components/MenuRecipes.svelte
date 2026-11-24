<script lang="ts">
	import { termText } from '$lib/text/terms';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import RecipeBreakdown from '../../recipes/components/RecipeBreakdown.svelte';
	import { goto } from '$app/navigation';
	import { recipeEditPath } from '$lib/nav/pages';
	import { recipeKey } from '../../recipes/recipe-key';
	import type { MenuDetailState } from '../menu-detail.svelte';
	import { menuDetailText } from '$lib/text/menu-detail';

	let { menu }: { menu: MenuDetailState } = $props();

	const branches = $derived(menu.sellers);
	const tabs = $derived(branches.map((branch) => ({ key: branch.id, label: branch.name })));
</script>

<Card flush>
	<CardHeader divided title={termText.recipe} description={menuDetailText.recipeDescription}>
		{#snippet actions()}
			{#if menu.recipes.canManage && menu.recipe}
				<Button label={menu.recipe.has_recipe ? menuDetailText.editRecipe : menuDetailText.fillRecipe} icon="pencil" variant="tertiary" disabled={menu.recipeLoading} onclick={() => menu.recipe && void goto(recipeEditPath(recipeKey.join(menu.recipe.menu_id, menu.recipe.outlet_id)))} />
			{/if}
		{/snippet}
	</CardHeader>
	{#if branches.length === 0}
		<Notice text={menuDetailText.notSoldAnywhere} />
	{:else}
		<Tabs {tabs} label={menuDetailText.recipeBranch} bind:value={() => menu.recipeBranch, (key) => menu.setRecipeBranch(key)} />
		<div class="p-4 tablet:p-5">
			{#if menu.recipeError}
				<Banner tone="danger" icon="alert-triangle">{menu.recipeError}</Banner>
			{:else if menu.recipe}
				<RecipeBreakdown recipe={menu.recipe} seesCost={menu.recipes.seesCost} />
			{:else}
				<Notice loading text={menuDetailText.recipeLoading} />
			{/if}
		</div>
	{/if}
</Card>

