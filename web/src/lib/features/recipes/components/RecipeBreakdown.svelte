<script lang="ts">
	import type { Recipe } from '$lib/api/types';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { EMPTY_VALUE, formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import { recipeText } from '$lib/text/recipes';
	import { format } from '$lib/text/format';

	let { recipe, seesCost }: { recipe: Recipe; seesCost: boolean } = $props();

	const money = (value: string | null) => (value === null ? EMPTY_VALUE : formatRupiah(value));

	const lines = $derived(
		recipe.lines.map((line) => ({ label: `${line.ingredient_name} · ${formatNumber(line.qty)} ${line.unit ?? ''}`.trim(), value: seesCost ? money(line.cost) : '' }))
	);
	const addCostLabel = $derived(
		format(recipeText.addCostLabel, { kind: recipe.add_cost_kind === 'persen' ? `${formatNumber(recipe.add_cost_value ?? 0)}%` : '', value: recipe.add_cost_custom ? ' (manual)' : '' }).trim()
	);
	const costs = $derived([
		{ label: recipeText.sellingPrice, value: money(recipe.price) },
		{ label: recipeText.totalIngredients, value: money(recipe.ingredients_cost) },
		{ label: addCostLabel, value: money(recipe.add_cost) },
		{ label: recipeText.overhead, value: money(recipe.overhead) },
		{ label: recipeText.finalCost, value: money(recipe.final_cost) },
		{
			label: recipeText.margin,
			value: `${money(recipe.margin)}${recipe.margin_percent !== null ? ` · ${formatPercentPlain(recipe.margin_percent)}` : ''}`,
			emphasis: recipe.margin !== null && Number(recipe.margin) < 0 ? ('bad' as const) : undefined
		},
		...(recipe.suggested_price !== null
			? [{ label: format(recipeText.suggestedPriceLabel, { percent: formatNumber(recipe.target_margin_percent ?? 0), custom: recipe.target_custom ? ', manual' : '' }), value: money(recipe.suggested_price) }]
			: [])
	]);
</script>

<div class="flex flex-col gap-4">
	<FigureList title={recipeText.ingredientsPerServing} figures={lines} empty={recipeText.noRecipesInBranch} />
	{#if seesCost && recipe.has_recipe}
		<FigureList title={recipeText.costAndMargin} figures={costs} />
	{/if}
</div>
