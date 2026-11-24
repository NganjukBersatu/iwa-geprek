<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Recipe, RecipeSave } from '$lib/api/types';
	import { access } from '$lib/auth/access.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureGrid from '$lib/components/card/FigureGrid.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { recipeKey } from '../recipe-key';
	import RecipeBreakdown from './RecipeBreakdown.svelte';
	import RecipeForm from './RecipeForm.svelte';
	import { recipeText } from '$lib/text/recipes';
	import { format } from '$lib/text/format';

	type RecipeContext = { branchCount: number };

	let { id }: { id: string } = $props();

	const key = untrack(() => recipeKey.split(id));
	const canManage = access.allows('manage_recipes');
	const seesCost = access.allows('see_recipe_costs');

	const detail = new RecordDetailState<Recipe, RecipeSave, RecipeContext>(untrack(() => id), {
		load: () => api.recipes.of(key.outletId, key.menuId),
		context: async () => {
			const branches = await branchList();
			return { branchCount: branches.length };
		},
		update: canManage
			? async (recipe, body) => {
					const result = await api.recipes.save(recipe.outlet_id, recipe.menu_id, body);
					const copied = result.copied.length > 0 ? `; ${result.copied.length} bahan baru disalin dengan stok 0` : '';
					if (result.branches > 1) toast.show(format(recipeText.recipeAlsoSaved, { name: recipe.menu_name, count: result.branches - 1, copied: copied }));
					return api.recipes.of(recipe.outlet_id, recipe.menu_id);
				}
			: undefined,
		name: (recipe) => recipe.menu_name,
		text: { ...recordText('resep', PAGES.recipes.label), saved: 'Resep {name} tersimpan.' }
	});
</script>

<RecordDetailView {detail} back={PAGES.recipes} trail={(recipe) => [{ label: PAGES.recipes.label, href: PAGES.recipes.path }, { label: recipe.menu_name }]} tables={['recipe_ingredients', 'recipe_add_costs', 'menu_items']} title={(recipe) => recipe.menu_name} description={(recipe) => `${recipe.outlet_name} · ${recipe.category_name ?? termText.noCategory}`}>
	{#snippet badge(recipe)}
		{#if !recipe.has_recipe}<Badge tone="warning">{recipeText.noRecipe}</Badge>{/if}
	{/snippet}
	{#snippet body(recipe)}
		<Card flush>
			<div class="p-4 tablet:p-5">
				<FigureGrid
					label={recipeText.menuSummary}
					figures={[
						{ label: termText.menu, value: recipe.menu_name },
						{ label: termText.category, value: recipe.category_name ?? EMPTY_VALUE },
						{ label: termText.branch, value: recipe.outlet_name },
						{ label: recipeText.sellingPrice, value: formatRupiah(recipe.price) }
					]}
				/>
			</div>
			<div class="border-t border-slate-100 p-4 tablet:p-5">
				<RecipeBreakdown {recipe} {seesCost} />
			</div>
		</Card>
	{/snippet}
	{#snippet form(props)}
		<RecipeForm recipe={props.record} {seesCost} canSpread={(props.context?.branchCount ?? 0) > 1} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={props.onsave} onclose={props.onclose} />
	{/snippet}
</RecordDetailView>
